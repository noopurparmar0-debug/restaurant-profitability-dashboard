#!/usr/bin/env python
# coding: utf-8

# # SkyCity Auckland Restaurants & Bars: Channel Profitability
# **Question:** which channel (In-Store, Uber Eats, DoorDash, Self-Delivery) really makes money?
# Steps: 1) load and check data, 2) validate profit formulas, 3) compare channels, 4) cost breakdown, 5) what-if tests, 6) cuisine/segment, 7) risk, 8) conclusions.

# In[1]:


import pandas as pd, numpy as np
import matplotlib.pyplot as plt, seaborn as sns
sns.set_theme(style="whitegrid")
pd.options.display.float_format = "{:,.2f}".format

df = pd.read_csv("SkyCity_Auckland_Restaurants___Bars.csv")
print(df.shape, "| missing values:", df.isna().sum().sum(), "| duplicate IDs:", df.RestaurantID.duplicated().sum())
df.head()


# ## 1. Quick data check

# In[2]:


df.describe().T[["min","mean","max"]]


# ## 2. Validate the profit formulas
# We rebuild each net profit from revenue, COGS, OPEX, commission and delivery cost and compare with the file. A difference under $0.01 is just rounding.

# In[3]:


base = 1 - df.COGSRate - df.OPEXRate          # margin before commission / delivery
check = pd.DataFrame({
    "In-Store":      df.InStoreRevenue*base - df.InStoreNetProfit,
    "Uber Eats":     df.UberEatsRevenue*(base-df.CommissionRate) - df.UberEatsNetProfit,
    "DoorDash":      df.DoorDashRevenue*(base-df.CommissionRate) - df.DoorDashNetProfit,
    "Self-Delivery": df.SelfDeliveryRevenue*base - df.SD_DeliveryTotalCost - df.SelfDeliveryNetProfit,
})
print("Largest formula difference ($):")
print(check.abs().max())
print("Orders add up:", (df[["InStoreOrders","UberEatsOrders","DoorDashOrders","SelfDeliveryOrders"]].sum(axis=1)==df.MonthlyOrders).all())
print("Delivery cost = orders x cost per order:", np.allclose(df.SelfDeliveryOrders*df.DeliveryCostPerOrder, df.SD_DeliveryTotalCost))


# All formulas in the dataset are correct, so we can trust the profit columns.

# ## 3. Build one tidy table (restaurant x channel)

# In[4]:


def build(df, comm_shift=0.0, cost_shift=0.0):
    comm = (df.CommissionRate + comm_shift).clip(lower=0)
    cost = (df.DeliveryCostPerOrder + cost_shift).clip(lower=0)
    parts = []
    for ch, o, r in [("In-Store","InStoreOrders","InStoreRevenue"),("Uber Eats","UberEatsOrders","UberEatsRevenue"),
                     ("DoorDash","DoorDashOrders","DoorDashRevenue"),("Self-Delivery","SelfDeliveryOrders","SelfDeliveryRevenue")]:
        t = df[["RestaurantID","CuisineType","Segment","Subregion"]].copy()
        t["Channel"] = ch
        t["Orders"], t["Revenue"] = df[o], df[r]
        t["COGS"], t["OPEX"] = t.Revenue*df.COGSRate, t.Revenue*df.OPEXRate
        t["Commission"] = t.Revenue*comm if "Uber" in ch or "Door" in ch else 0.0
        t["Delivery"] = t.Orders*cost if ch == "Self-Delivery" else 0.0
        t["Profit"] = t.Revenue - t.COGS - t.OPEX - t.Commission - t.Delivery
        t["Margin %"] = t.Profit/t.Revenue*100
        t["Profit/Order"] = t.Profit/t.Orders
        parts.append(t)
    return pd.concat(parts, ignore_index=True)

def summary(t, by="Channel"):
    g = t.groupby(by)[["Orders","Revenue","COGS","OPEX","Commission","Delivery","Profit"]].sum()
    g["Margin %"] = g.Profit/g.Revenue*100
    g["Profit/Order"] = g.Profit/g.Orders
    g["Commission Drag %"] = np.where(g.Commission>0, g.Commission/(g.Profit+g.Commission)*100, 0)
    return g

long = build(df)
order = ["In-Store","Uber Eats","DoorDash","Self-Delivery"]
S = summary(long).loc[order]
S


# ## 4. Channel comparison: volume vs profit

# In[5]:


fig, ax = plt.subplots(1, 3, figsize=(16, 4))
S["Margin %"].plot.bar(ax=ax[0], color="teal", title="Net margin (%)")
S["Profit/Order"].plot.bar(ax=ax[1], color="orange", title="Net profit per order ($)")
(S[["Orders","Profit"]]/S[["Orders","Profit"]].sum()*100).plot.bar(ax=ax[2], title="Share of orders vs share of profit (%)")
for a in ax: a.set_xlabel(""); a.tick_params(axis="x", rotation=20)
plt.tight_layout(); plt.show()


# **Finding:** Uber Eats and DoorDash bring about 61% of all orders, but almost no profit. In-Store earns the best margin, and Self-Delivery is a close second.

# ## 5. Cost breakdown and margin waterfall

# In[6]:


pct = S[["COGS","OPEX","Commission","Delivery","Profit"]].div(S.Revenue, axis=0)*100
pct.plot.bar(stacked=True, figsize=(9,4), color=["#8d99ae","#adb5bd","#e76f51","#f4a261","#2a9d8f"])
plt.ylabel("% of revenue"); plt.title("Where each $100 of revenue goes"); plt.xticks(rotation=20); plt.show()
pct.round(1)


# In[7]:


def waterfall(ch, ax):
    r = S.loc[ch]
    items = [("Revenue", r.Revenue), ("COGS", -r.COGS), ("OPEX", -r.OPEX)]
    if r.Commission: items.append(("Commission", -r.Commission))
    if r.Delivery:   items.append(("Delivery", -r.Delivery))
    run = 0
    for label, v in items:
        ax.bar(label, abs(v), bottom=run if v > 0 else run + v, color="#2a9d8f" if v > 0 else "#e76f51")
        run += v
    ax.bar("Net profit", run, color="#264653")
    ax.set_title(f"{ch} ($)"); ax.tick_params(axis="x", rotation=30)

fig, axes = plt.subplots(1, 4, figsize=(18, 4))
for ch, ax in zip(order, axes): waterfall(ch, ax)
plt.tight_layout(); plt.show()


# **Commission Drag Index** = commission ÷ profit before commission. **Self-Delivery ROI** = net profit ÷ delivery cost.

# In[8]:


print(S.loc[["Uber Eats","DoorDash"], "Commission Drag %"].round(1))
print("Self-delivery ROI: $%.2f profit per $1 of delivery cost" % (S.loc["Self-Delivery","Profit"]/S.loc["Self-Delivery","Delivery"]))


# ## 6. What-if: commission and delivery cost
# **Breakeven logic**
# - An aggregator order loses money when `CommissionRate > 1 - COGS - OPEX`.
# - Self-delivery beats an aggregator while `cost per order < AOV x CommissionRate`.

# In[9]:


d = df.assign(pre_margin = 1-df.COGSRate-df.OPEXRate, be_cost = df.AOV*df.CommissionRate)
print("Avg margin before commission: %.1f%%" % (d.pre_margin.mean()*100))
print("Restaurants losing money on aggregators: %.0f%%" % ((d.CommissionRate>d.pre_margin).mean()*100))
print("Self-delivery breakeven cost vs aggregator: $%.2f per order (actual average $%.2f, max $%.2f)" %
      (d.be_cost.mean(), d.DeliveryCostPerOrder.mean(), d.DeliveryCostPerOrder.max()))


# In[10]:


fig, ax = plt.subplots(1, 2, figsize=(13,4))
pts = [(p, summary(build(df, p/100)).loc[c, "Margin %"], c) for p in range(-10,11,2) for c in ["Uber Eats","DoorDash"]]
sns.lineplot(data=pd.DataFrame(pts, columns=["Commission change (pts)","Margin %","Channel"]),
             x="Commission change (pts)", y="Margin %", hue="Channel", marker="o", ax=ax[0]); ax[0].set_title("Aggregator margin vs commission")
pts = [(x, summary(build(df, 0, x)).loc["Self-Delivery","Margin %"]) for x in range(0,13)]
ax[1].plot(*zip(*pts), marker="o"); ax[1].set_title("Self-delivery margin vs extra cost per order"); ax[1].set_xlabel("Extra $ per order"); ax[1].set_ylabel("Margin %")
plt.tight_layout(); plt.show()


# ## 7. Cuisine and segment comparison

# In[11]:


fig, ax = plt.subplots(1, 2, figsize=(15,5))
for a, dim in zip(ax, ["CuisineType","Segment"]):
    h = summary(long, [dim,"Channel"])["Margin %"].unstack()[order]
    sns.heatmap(h, annot=True, fmt=".1f", cmap="RdYlGn", center=15, ax=a); a.set_title(f"Margin % by {dim}")
plt.tight_layout(); plt.show()


# In[12]:


h = summary(long, ["Segment","Channel"])["Margin %"].unstack()[order]
print("Most fragile segment on aggregators:", h[["Uber Eats","DoorDash"]].mean(axis=1).idxmin())
print("Most resilient segment on aggregators:", h[["Uber Eats","DoorDash"]].mean(axis=1).idxmax())


# ## 8. Risk and volatility

# In[13]:


sns.boxplot(data=long, x="Channel", y="Margin %", order=order); plt.axhline(0, color="red", ls="--"); plt.title("Margin spread across restaurants"); plt.show()
risk = long.groupby("Channel")["Margin %"].agg(Average="mean", Volatility="std", Worst_5pct=lambda x: x.quantile(.05))
risk["Loss-making %"] = long.groupby("Channel")["Margin %"].apply(lambda x: (x<0).mean()*100)
risk.loc[order]


# ## 9. Conclusions and recommendations
# 1. **Volume is not profit.** Aggregators take most orders but make under 1% margin, while In-Store and Self-Delivery make 20%+.
# 2. **Commission is the cause.** Platforms take almost all profit that exists before commission (see drag index).
# 3. **Renegotiate.** Roughly a third of restaurants lose money on aggregator orders. Evidence for lowering the commission or negotiating tiers.
# 4. **Self-delivery pays.** Its cost per order is far below the breakeven cost, so moving orders to self-delivery lifts profit.
# 5. **Watch fragile groups.** Look at the heatmaps for cuisines/segments with the lowest aggregator margin (high-COGS or high-OPEX models like Full-service).
# 6. **Use the Streamlit dashboard** to test commission and delivery-cost changes live.
