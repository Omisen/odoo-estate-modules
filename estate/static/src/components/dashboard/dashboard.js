import { Component, onWillStart, useState } from "@odoo/owl";
import { formatCurrency } from "@web/core/currency";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

export class EstateDashboard extends Component {
    static template = "estate.Dashboard";
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({
            loading: true,
            error: null,
            currencyId: null,
            propertyNewCount: 0,
            propertyOfferReceivedCount: 0,
            propertySoldCount: 0,
            pendingOfferCount: 0,
            avgSellingPrice: 0,
            priceTrendPoints: [],
            yAxisGuides: [],
            svgPoints: "",
        });

        onWillStart(async () => {
            await this.loadDashboard();
        });
    }

    async loadDashboard() {
        try {
            const currentCompanyId = session.user_companies.current_company;
            const [company] = await this.orm.read("res.company", [currentCompanyId], ["currency_id"]);
            this.state.currencyId = company?.currency_id?.[0] || null;

            const [
                propertyNewCount,
                propertyOfferReceivedCount,
                propertySoldCount,
                pendingOfferCount,
                soldProperties,
                offers,
            ] = await Promise.all([
                this.orm.searchCount("estate.property", [["status", "=", "new"]]),
                this.orm.searchCount("estate.property", [["status", "=", "offer_recieved"]]),
                this.orm.searchCount("estate.property", [["status", "=", "sold"]]),
                this.orm.searchCount("estate.property.offer", [["status", "=", "new"]]),
                this.orm.searchRead(
                    "estate.property",
                    [["status", "=", "sold"], ["selling_price", ">", 0]],
                    ["selling_price"]
                ),
                this.orm.searchRead(
                    "estate.property.offer",
                    [["create_date", "!=", false]],
                    ["create_date", "price"],
                    { order: "create_date asc" }
                ),
            ]);

            const totalSellingPrice = soldProperties.reduce(
                (sum, property) => sum + (property.selling_price || 0),
                0
            );

            this.state.propertyNewCount = propertyNewCount;
            this.state.propertyOfferReceivedCount = propertyOfferReceivedCount;
            this.state.propertySoldCount = propertySoldCount;
            this.state.pendingOfferCount = pendingOfferCount;
            this.state.avgSellingPrice = soldProperties.length
                ? totalSellingPrice / soldProperties.length
                : 0;

            this.buildTrendChart(offers);
        } catch (error) {
            this.state.error = error.message || "Unable to load estate dashboard.";
        } finally {
            this.state.loading = false;
        }
    }

    buildTrendChart(offers) {
        const monthlyBuckets = new Map();
        for (const offer of offers) {
            const createdAt = new Date(offer.create_date);
            const bucketKey = `${createdAt.getFullYear()}-${String(createdAt.getMonth() + 1).padStart(2, "0")}`;
            if (!monthlyBuckets.has(bucketKey)) {
                monthlyBuckets.set(bucketKey, {
                    label: createdAt.toLocaleDateString(undefined, { month: "short", year: "numeric" }),
                    total: 0,
                    count: 0,
                });
            }
            const bucket = monthlyBuckets.get(bucketKey);
            bucket.total += offer.price || 0;
            bucket.count += 1;
        }

        const points = [...monthlyBuckets.values()]
            .slice(-8)
            .filter((bucket) => bucket.count)
            .map((bucket) => ({
                label: bucket.label,
                value: Number((bucket.total / bucket.count).toFixed(2)),
            }));

        this.state.priceTrendPoints.splice(0, this.state.priceTrendPoints.length, ...points);

        if (!points.length) {
            this.state.yAxisGuides.splice(0, this.state.yAxisGuides.length);
            this.state.svgPoints = "";
            return;
        }

        const width = 680;
        const height = 240;
        const paddingX = 42;
        const paddingY = 28;
        const values = points.map((point) => point.value);
        let maxValue = Math.max(...values);
        let minValue = Math.min(...values);
        if (maxValue === minValue) {
            maxValue += 1;
            minValue = Math.max(0, minValue - 1);
        }
        const usableWidth = width - paddingX * 2;
        const usableHeight = height - paddingY * 2;
        const stepX = usableWidth / Math.max(points.length - 1, 1);
        const toY = (amount) => {
            const ratio = (amount - minValue) / (maxValue - minValue);
            return height - paddingY - ratio * usableHeight;
        };

        this.state.svgPoints = points
            .map((point, index) => `${(paddingX + stepX * index).toFixed(2)},${toY(point.value).toFixed(2)}`)
            .join(" ");

        const guides = [];
        for (let step = 0; step < 4; step++) {
            const value = minValue + ((maxValue - minValue) * step) / 3;
            guides.push({ value: Math.round(value), y: toY(value) });
        }
        this.state.yAxisGuides.splice(0, this.state.yAxisGuides.length, ...guides);
    }

    get hasChartData() {
        return this.state.priceTrendPoints.length > 0;
    }

    get formattedAverageSellingPrice() {
        return formatCurrency(this.state.avgSellingPrice, this.state.currencyId);
    }

    get chartCircles() {
        const width = 680;
        const paddingX = 42;
        const pointsCount = Math.max(this.state.priceTrendPoints.length - 1, 1);
        const usableWidth = width - paddingX * 2;
        return this.state.priceTrendPoints.map((point, index) => {
            const [x, y] = this.state.svgPoints.split(" ")[index].split(",").map(Number);
            return { key: `${point.label}-${index}`, x, y, label: point.label, value: point.value };
        });
    }

    openPropertyAction(domain, name) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: "estate.property",
            view_mode: "list,form,kanban",
            views: [[false, "list"], [false, "form"], [false, "kanban"]],
            domain,
            target: "current",
        });
    }

    openOfferAction(domain, name) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: "estate.property.offer",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain,
            target: "current",
        });
    }

    openNewProperties() {
        this.openPropertyAction([["status", "=", "new"]], "New Properties");
    }

    openOfferReceivedProperties() {
        this.openPropertyAction([["status", "=", "offer_recieved"]], "Offer Received Properties");
    }

    openSoldProperties() {
        this.openPropertyAction([["status", "=", "sold"]], "Sold Properties");
    }

    openPendingOffers() {
        this.openOfferAction([["status", "=", "new"]], "Pending Offers");
    }
}

registry.category("actions").add("estate.dashboard_action", EstateDashboard);