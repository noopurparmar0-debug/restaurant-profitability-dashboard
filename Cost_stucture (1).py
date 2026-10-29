import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
df=pd.read_csv(r"C:\Users\HP\Downloads\SkyCity Auckland Restaurants & Bars.csv")
df.head()
df.duplicated().sum()
df.head
df.columns.tolist()
# ============================================================
# PROJECT CALCULATION VALIDATION
# Restaurant Profitability Analysis
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display

# ------------------------------------------------------------
# STEP 1: PREPARE DATA
# ------------------------------------------------------------

data = df.copy()

channels = {
    "In-Store": {
        "revenue": "InStoreRevenue",
        "profit": "InStoreNetProfit",
        "orders": "InStoreOrders"
    },
    "Uber Eats": {
        "revenue": "UberEatsRevenue",
        "profit": "UberEatsNetProfit",
        "orders": "UberEatsOrders"
    },
    "DoorDash": {
        "revenue": "DoorDashRevenue",
        "profit": "DoorDashNetProfit",
        "orders": "DoorDashOrders"
    },
    "Self-Delivery": {
        "revenue": "SelfDeliveryRevenue",
        "profit": "SelfDeliveryNetProfit",
        "orders": "SelfDeliveryOrders"
    }
}

# Check required columns

required_columns = [
    "RestaurantID",
    "RestaurantName"
]

for channel, info in channels.items():
    required_columns.append(info["revenue"])
    required_columns.append(info["profit"])
    required_columns.append(info["orders"])

missing_columns = [
    col for col in required_columns
    if col not in data.columns
]

if missing_columns:
    raise ValueError(
        "Missing columns in dataset: " + str(missing_columns)
    )

# Convert relevant columns to numeric

for channel, info in channels.items():
    for key in ["revenue", "profit", "orders"]:
        col = info[key]
        data[col] = pd.to_numeric(
            data[col],
            errors="coerce"
        )

print("Dataset prepared successfully.")

# ------------------------------------------------------------
# REQUIREMENT 1:
# VALIDATE PROVIDED VS ACTUAL PROFIT PERFORMANCE
# ------------------------------------------------------------

# Check whether the dataset contains the cost columns
# required to recalculate profit.

cost_columns = [
    "COGSRate",
    "OPEXRate",
    "CommissionRate",
    "DeliveryCostPerOrder"
]

missing_cost_columns = [
    col for col in cost_columns
    if col not in data.columns
]

if missing_cost_columns:
    print(
        "\nProfit recalculation is not possible because "
        "these cost columns are missing:",
        missing_cost_columns
    )

    validation_df = pd.DataFrame()

else:

    for col in cost_columns:
        data[col] = pd.to_numeric(
            data[col],
            errors="coerce"
        )

    # Convert percentage rates to decimals if necessary.
    # Example: 25 becomes 0.25.
    for col in [
        "COGSRate",
        "OPEXRate",
        "CommissionRate"
    ]:
        valid_rates = data[col].dropna()

        if (
            not valid_rates.empty
            and valid_rates.median() > 1
        ):
            data[col] = data[col] / 100

    validation_records = []

    for channel, info in channels.items():

        revenue = data[info["revenue"]]
        profit = data[info["profit"]]
        orders = data[info["orders"]]

        # Assumed profit formulas.
        # Confirm these formulas against your dataset's
        # original profit calculation methodology.

        if channel == "In-Store":

            estimated_profit = revenue * (
                1 - data["COGSRate"] - data["OPEXRate"]
            )

        elif channel in ["Uber Eats", "DoorDash"]:

            estimated_profit = revenue * (
                1
                - data["COGSRate"]
                - data["OPEXRate"]
                - data["CommissionRate"]
            )

        else:

            estimated_profit = (
                revenue
                * (
                    1
                    - data["COGSRate"]
                    - data["OPEXRate"]
                )
                - orders * data["DeliveryCostPerOrder"]
            )

        difference = profit - estimated_profit

        comparison = pd.DataFrame({
            "Provided Profit": profit,
            "Estimated Profit": estimated_profit,
            "Difference": difference
        }).dropna()

        if not comparison.empty:

            validation_records.append({
                "Channel": channel,
                "Restaurants Compared": len(comparison),
                "Provided Total Profit":
                    comparison["Provided Profit"].sum(),
                "Estimated Total Profit":
                    comparison["Estimated Profit"].sum(),
                "Total Difference":
                    comparison["Difference"].sum(),
                "Average Absolute Difference":
                    comparison["Difference"].abs().mean(),
                "Matching Rows":
                    (
                        comparison["Difference"].abs() < 0.01
                    ).sum()
            })

    validation_df = pd.DataFrame(validation_records)

    print("\n1. PROFIT VALIDATION RESULTS")

    if not validation_df.empty:

        display(validation_df.round(2))

        # Comparison chart

        x = np.arange(len(validation_df))
        width = 0.35

        plt.figure(figsize=(10, 5))

        plt.bar(
            x - width / 2,
            validation_df["Provided Total Profit"],
            width,
            label="Provided Profit"
        )

        plt.bar(
            x + width / 2,
            validation_df["Estimated Total Profit"],
            width,
            label="Estimated Profit"
        )

        plt.xticks(
            x,
            validation_df["Channel"],
            rotation=15
        )

        plt.title("Provided vs Estimated Profit")
        plt.xlabel("Sales Channel")
        plt.ylabel("Total Profit")
        plt.legend()
        plt.tight_layout()
        plt.show()

    else:
        print("No valid records available for profit validation.")

# ------------------------------------------------------------
# REQUIREMENT 2:
# NORMALIZE PROFIT ON A PER-ORDER BASIS
# ------------------------------------------------------------

per_order_records = []

for channel, info in channels.items():

    revenue_col = info["revenue"]
    profit_col = info["profit"]
    orders_col = info["orders"]

    channel_data = data[
        [revenue_col, profit_col, orders_col]
    ].dropna()

    # Use only records with positive order counts.

    channel_data = channel_data[
        channel_data[orders_col] > 0
    ]

    total_orders = channel_data[orders_col].sum()
    total_revenue = channel_data[revenue_col].sum()
    total_profit = channel_data[profit_col].sum()

    if total_orders > 0:

        revenue_per_order = total_revenue / total_orders
        profit_per_order = total_profit / total_orders

    else:

        revenue_per_order = np.nan
        profit_per_order = np.nan

    per_order_records.append({
        "Channel": channel,
        "Total Orders": total_orders,
        "Total Revenue": total_revenue,
        "Total Net Profit": total_profit,
        "Revenue Per Order": revenue_per_order,
        "Profit Per Order": profit_per_order
    })

per_order_df = pd.DataFrame(per_order_records)

print("\n2. PROFIT PER ORDER COMPARISON")

display(per_order_df.round(2))

# Profit per order chart

plot_data = per_order_df.dropna(
    subset=["Profit Per Order"]
)

if not plot_data.empty:

    plt.figure(figsize=(9, 5))

    plt.bar(
        plot_data["Channel"],
        plot_data["Profit Per Order"]
    )

    plt.axhline(
        y=0,
        linestyle="--",
        label="Break-even"
    )

    plt.title("Net Profit Per Order by Channel")
    plt.xlabel("Sales Channel")
    plt.ylabel("Profit Per Order")
    plt.legend()
    plt.tight_layout()
    plt.show()

# ------------------------------------------------------------
# REQUIREMENT 3:
# IDENTIFY OUTLIERS IN EXTREME PROFIT MARGINS
# ------------------------------------------------------------

# Calculate margin for each restaurant and channel.

for channel, info in channels.items():

    revenue = data[info["revenue"]]
    profit = data[info["profit"]]

    margin_col = channel + "_Margin"

    data[margin_col] = np.where(
        revenue > 0,
        (profit / revenue) * 100,
        np.nan
    )

outlier_records = []

for channel in channels:

    margin_col = channel + "_Margin"
    margins = data[margin_col].dropna()

    if len(margins) < 4:
        print(
            f"Not enough data for outlier analysis: {channel}"
        )
        continue

    # Interquartile Range (IQR) method

    Q1 = margins.quantile(0.25)
    Q3 = margins.quantile(0.75)

    IQR = Q3 - Q1

    lower_limit = Q1 - 1.5 * IQR
    upper_limit = Q3 + 1.5 * IQR

    for index, row in data.iterrows():

        margin = row[margin_col]

        if pd.isna(margin):
            continue

        if margin < lower_limit or margin > upper_limit:

            if margin < lower_limit:
                outlier_type = "Extreme Low Margin"
            else:
                outlier_type = "Extreme High Margin"

            outlier_records.append({
                "RestaurantID": row["RestaurantID"],
                "RestaurantName": row["RestaurantName"],
                "Channel": channel,
                "Profit Margin (%)": margin,
                "Lower Limit (%)": lower_limit,
                "Upper Limit (%)": upper_limit,
                "Outlier Type": outlier_type
            })

outliers_df = pd.DataFrame(outlier_records)

print("\n3. EXTREME PROFIT MARGIN OUTLIERS")

if outliers_df.empty:

    print("No extreme margin outliers detected.")

else:

    outliers_df = outliers_df.sort_values(
        by="Profit Margin (%)",
        ascending=True
    )

    display(outliers_df.round(2))

# ------------------------------------------------------------
# OUTLIER VISUALIZATION
# ------------------------------------------------------------

margin_data = []

for channel in channels:
    margin_data.append(
        data[channel + "_Margin"].dropna()
    )

plt.figure(figsize=(10, 6))

plt.boxplot(
    margin_data,
    tick_labels=list(channels.keys()),
    showmeans=True
)

plt.axhline(
    y=0,
    linestyle="--",
    label="Break-even Margin"
)

plt.title("Profit Margin Outlier Analysis")
plt.xlabel("Sales Channel")
plt.ylabel("Profit Margin (%)")
plt.legend()
plt.tight_layout()
plt.show()

# ------------------------------------------------------------
# FINAL PROJECT SUMMARY
# ------------------------------------------------------------

print("\n========== FINAL PROJECT SUMMARY ==========")

valid_channels = per_order_df.dropna(
    subset=["Profit Per Order"]
)

if not valid_channels.empty:

    best_channel = valid_channels.loc[
        valid_channels["Profit Per Order"].idxmax(),
        "Channel"
    ]

    lowest_channel = valid_channels.loc[
        valid_channels["Profit Per Order"].idxmin(),
        "Channel"
    ]

    print("Highest Profit Per Order:", best_channel)
    print("Lowest Profit Per Order:", lowest_channel)

print("Total Margin Outliers:", len(outliers_df))

print("\nProject Calculation Validation Completed.")



# Calculate revenue and profit for each channel

revenue = {
    'In-Store': df['InStoreRevenue'].sum(),
    'Uber Eats': df['UberEatsRevenue'].sum(),
    'DoorDash': df['DoorDashRevenue'].sum(),
    'Self Delivery': df['SelfDeliveryRevenue'].sum()
}

profit = {
    'In-Store': df['InStoreNetProfit'].sum(),
    'Uber Eats': df['UberEatsNetProfit'].sum(),
    'DoorDash': df['DoorDashNetProfit'].sum(),
    'Self Delivery': df['SelfDeliveryNetProfit'].sum()
}

# Calculate profit margin

profit_margin = {}

for channel in revenue:
    if revenue[channel] != 0:
        profit_margin[channel] = (
            profit[channel] / revenue[channel]
        ) * 100
    else:
        profit_margin[channel] = 0

# Display bar chart

plt.figure(figsize=(9, 5))

plt.bar(profit_margin.keys(), profit_margin.values())

plt.title('Profit Margin Comparison by Channel')
plt.xlabel('Sales Channel')
plt.ylabel('Profit Margin (%)')

plt.xticks(rotation=15)
plt.tight_layout()
plt.show()





import matplotlib.pyplot as plt

# Calculate net profit per order for each channel
in_store_profit = df["InStoreNetProfit"].sum() / df["InStoreOrders"].sum()

uber_profit = df["UberEatsNetProfit"].sum() / df["UberEatsOrders"].sum()

door_profit = df["DoorDashNetProfit"].sum() / df["DoorDashOrders"].sum()

self_profit = df["SelfDeliveryNetProfit"].sum() / df["SelfDeliveryOrders"].sum()

# Store the results
channels = ["In-Store", "Uber Eats", "DoorDash", "Self-Delivery"]

profit_per_order = [
    in_store_profit,
    uber_profit,
    door_profit,
    self_profit
]

# Print the results
for i in range(len(channels)):
    print(channels[i], "Net Profit per Order: $", round(profit_per_order[i], 2))

# Create the bar chart
plt.figure(figsize=(9, 5))

plt.bar(channels, profit_per_order)

plt.title("Net Profit per Order by Channel")
plt.xlabel("Sales Channel")
plt.ylabel("Net Profit per Order ($)")

plt.tight_layout()
plt.show()







import matplotlib.pyplot as plt

# Calculate total net profit for each channel
channel_profit = {
    'In-Store': df['InStoreNetProfit'].sum(),
    'Uber Eats': df['UberEatsNetProfit'].sum(),
    'DoorDash': df['DoorDashNetProfit'].sum(),
    'Self Delivery': df['SelfDeliveryNetProfit'].sum()
}

# Create KPI cards
fig, axes = plt.subplots(1, 4, figsize=(14, 3))

for ax, (channel, profit) in zip(axes, channel_profit.items()):

    # Display profit value
    ax.text(
        0.5, 0.55,
        '${:.2f}M'.format(profit / 1000000),
        ha='center',
        va='center',
        fontsize=18,
        fontweight='bold'
    )

    # Display channel name
    ax.set_title(channel, fontsize=12)

    # Hide axes
    ax.axis('off')

plt.suptitle('Net Profit by Channel', fontsize=16)
plt.tight_layout()
plt.show()




#Compare Absolute Profit VS Margin Efficiency


# Calculate total revenue for each channel
revenue = {
    'In-Store': df['InStoreRevenue'].sum(),
    'Uber Eats': df['UberEatsRevenue'].sum(),
    'DoorDash': df['DoorDashRevenue'].sum(),
    'Self Delivery': df['SelfDeliveryRevenue'].sum()
}

# Calculate total net profit for each channel
profit = {
    'In-Store': df['InStoreNetProfit'].sum(),
    'Uber Eats': df['UberEatsNetProfit'].sum(),
    'DoorDash': df['DoorDashNetProfit'].sum(),
    'Self Delivery': df['SelfDeliveryNetProfit'].sum()
}

# Calculate profit margin percentage
margin = {}

for channel in revenue:
    if revenue[channel] != 0:
        margin[channel] = (profit[channel] / revenue[channel]) * 100
    else:
        margin[channel] = 0

# Create a summary table
comparison = pd.DataFrame({
    'Channel': list(profit.keys()),
    'Absolute Profit': list(profit.values()),
    'Profit Margin (%)': list(margin.values())
})

print("Absolute Profit vs Margin Efficiency")
print(comparison.round(2))

# Create two comparison charts
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Chart 1: Absolute Profit
axes[0].bar(comparison['Channel'], comparison['Absolute Profit'])
axes[0].set_title('Absolute Profit by Channel')
axes[0].set_xlabel('Sales Channel')
axes[0].set_ylabel('Total Net Profit')
axes[0].tick_params(axis='x', rotation=20)

# Chart 2:  Margin efficiency
axes[1].bar(comparison['Channel'], comparison['Profit Margin (%)'])
axes[1].set_title('Margin Efficiency by Channel')
axes[1].set_xlabel('Sales Channel')
axes[1].set_ylabel('Profit Margin (%)')
axes[1].tick_params(axis='x', rotation=20)

plt.tight_layout()
plt.show()




# Cost components Decomposition 
 # Break down revenue into:
    # -COGS Impact    #-Commission drag(Uber Eats,DoorDash)
    #-OPEX Impact     #-Delivery cost (self_Delivery)import pandas as pd
 # Visualize cost waterfalls per channel import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, clear_output

# Revenue columns for each channel
channels = {
    'In-Store': 'InStoreRevenue',
    'Uber Eats': 'UberEatsRevenue',
    'DoorDash': 'DoorDashRevenue',
    'Self-Delivery': 'SelfDeliveryRevenue'
}

# Net profit columns
profit_columns = {
    'In-Store': 'InStoreNetProfit',
    'Uber Eats': 'UberEatsNetProfit',
    'DoorDash': 'DoorDashNetProfit',
    'Self-Delivery': 'SelfDeliveryNetProfit'
}

# Create dropdown list
channel_dropdown = widgets.Dropdown(
    options=list(channels.keys()),
    value='In-Store',
    description='Select Channel:'
)

# Create output area
output = widgets.Output()


def show_analysis(channel):

    revenue_col = channels[channel]

    # Calculate revenue
    revenue = df[revenue_col].sum()

    # Calculate COGS and OPEX
    cogs = (df[revenue_col] * df['COGSRate']).sum()
    opex = (df[revenue_col] * df['OPEXRate']).sum()

    # Set default costs
    commission = 0
    delivery_cost = 0

    # Calculate commission for delivery apps
    if channel in ['Uber Eats', 'DoorDash']:
        commission = (
            df[revenue_col] * df['CommissionRate']
        ).sum()

    # Calculate self-delivery cost
    if channel == 'Self-Delivery':
        delivery_cost = df['SD_DeliveryTotalCost'].sum()

    # Calculate net profit from dataset
    profit = df[profit_columns[channel]].sum()

    # Store results in a table
    cost_summary = pd.DataFrame({
        'Metric': [
            'Revenue',
            'COGS',
            'OPEX',
            'Commission',
            'Delivery Cost',
            'Net Profit'
        ],
        'Amount': [
            revenue,
            cogs,
            opex,
            commission,
            delivery_cost,
            profit
        ]
    })

    print('Cost Analysis for:', channel)
    display(cost_summary.round(2))


# Update results when dropdown changes
def update_analysis(change):

    if change['name'] == 'value':
        with output:
            clear_output(wait=True)
            show_analysis(change['new'])


# Connect dropdown to function
channel_dropdown.observe(update_analysis, names='value')

# Display dropdown and results
display(channel_dropdown, output)

# Show default channel analysis
with output:
    show_analysis(channel_dropdown.value)







    # Cost components Decomposition 
 # Break down revenue into:
    # -COGS Impact    #-Commission drag(Uber Eats,DoorDash)
    #-OPEX Impact     #-Delivery cost (self_Delivery)import pandas as pd
 # Visualize cost waterfalls per channel 
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, clear_output

# Channel dropdown list
channel_dropdown = widgets.Dropdown(
    options=['In-Store', 'Uber Eats', 'DoorDash', 'Self-Delivery'],
    value='In-Store',
    description='Select Channel:'
)

output = widgets.Output()

# Revenue columns
revenue_columns = {
    'In-Store': 'InStoreRevenue',
    'Uber Eats': 'UberEatsRevenue',
    'DoorDash': 'DoorDashRevenue',
    'Self-Delivery': 'SelfDeliveryRevenue'
}

# Net profit columns
profit_columns = {
    'In-Store': 'InStoreNetProfit',
    'Uber Eats': 'UberEatsNetProfit',
    'DoorDash': 'DoorDashNetProfit',
    'Self-Delivery': 'SelfDeliveryNetProfit'
}


def show_analysis(channel):

    revenue_col = revenue_columns[channel]

    # Calculate revenue and costs
    revenue = df[revenue_col].sum()

    cogs = (df[revenue_col] * df['COGSRate']).sum()
    opex = (df[revenue_col] * df['OPEXRate']).sum()

    commission = 0
    delivery_cost = 0

    if channel in ['Uber Eats', 'DoorDash']:
        commission = (
            df[revenue_col] * df['CommissionRate']
        ).sum()

    if channel == 'Self-Delivery':
        delivery_cost = df['SD_DeliveryTotalCost'].sum()

    # Create a temporary cost table
    cost_data = df[['CuisineType']].copy()

    cost_data['COGS'] = df[revenue_col] * df['COGSRate']
    cost_data['OPEX'] = df[revenue_col] * df['OPEXRate']
    cost_data['Commission'] = 0
    cost_data['Delivery Cost'] = 0

    if channel in ['Uber Eats', 'DoorDash']:
        cost_data['Commission'] = (
            df[revenue_col] * df['CommissionRate']
        )

    if channel == 'Self-Delivery':
        cost_data['Delivery Cost'] = df['SD_DeliveryTotalCost']

    # Group costs by cuisine type
    cuisine_costs = cost_data.groupby('CuisineType')[
        ['COGS', 'OPEX', 'Commission', 'Delivery Cost']
    ].sum()

    print('Cost Components by Cuisine Type')
    display(cuisine_costs.round(2))

    # Chart 1: Cost Components by Cuisine Type
    cuisine_costs.plot(kind='bar', figsize=(12, 6))

    plt.title('Cost Components by Cuisine Type - ' + channel)
    plt.xlabel('Cuisine Type')
    plt.ylabel('Total Cost')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

    # Prepare waterfall chart
    labels = ['Revenue', 'COGS', 'OPEX']
    values = [revenue, cogs, opex]

    if channel in ['Uber Eats', 'DoorDash']:
        labels.append('Commission')
        values.append(commission)

    if channel == 'Self-Delivery':
        labels.append('Delivery Cost')
        values.append(delivery_cost)

    # Calculate profit after the listed costs
    calculated_profit = revenue - sum(values[1:])

    # Waterfall chart
    plt.figure(figsize=(8, 5))

    # Revenue bar
    plt.bar(labels[0], revenue)

    running_total = revenue

    # Cost bars
    for label, cost in zip(labels[1:], values[1:]):
        new_total = running_total - cost

        plt.bar(
            label,
            cost,
            bottom=new_total
        )

        running_total = new_total

    # Final profit bar
    plt.bar('Calculated Profit', calculated_profit)

    plt.title('Waterfall Chart - ' + channel)
    plt.xlabel('Revenue and Cost Components')
    plt.ylabel('Amount')
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.show()

    # Display profit information
    actual_profit = df[profit_columns[channel]].sum()

    print('Total Revenue:', round(revenue, 2))
    print('Calculated Profit:', round(calculated_profit, 2))
    print('Net Profit from Dataset:', round(actual_profit, 2))


def update_analysis(change):

    if change['name'] == 'value':
        with output:
            clear_output(wait=True)
            show_analysis(change['new'])


# Connect dropdown to the analysis
channel_dropdown.observe(update_analysis, names='value')

# Display dropdown
display(channel_dropdown, output)

# Show the first analysis
with output:
    show_analysis(channel_dropdown.value)



    import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ipywidgets as widgets

from IPython.display import display, clear_output, HTML

# ==========================================
# COMMISSION & DELIVERY COST IMPACT ANALYSIS
# ==========================================

data = df.copy()

# Required columns
required_columns = [
    "CommissionRate",
    "DeliveryCostPerOrder",
    "UberEatsOrders",
    "DoorDashOrders",
    "SelfDeliveryOrders",
    "UberEatsRevenue",
    "DoorDashRevenue",
    "UberEatsNetProfit",
    "DoorDashNetProfit",
    "SelfDeliveryNetProfit"
]

missing_columns = [
    col for col in required_columns if col not in data.columns
]

if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")

# Convert required columns to numeric
for col in required_columns:
    data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0)

# ==========================================
# DASHBOARD TITLE
# ==========================================

display(HTML("""
<h1 style='text-align:center; color:#1F4E78;'>
Commission & Delivery Cost Impact Analysis
</h1>
<p style='text-align:center; font-size:15px;'>
Restaurant Profitability Dashboard
</p>
<hr>
"""))

# ==========================================
# INTERACTIVE SLIDERS
# ==========================================

commission_slider = widgets.IntSlider(
    value=0,
    min=-20,
    max=20,
    step=1,
    description="Commission Change:",
    style={"description_width": "initial"},
    layout=widgets.Layout(width="500px")
)

delivery_slider = widgets.FloatSlider(
    value=0,
    min=0,
    max=10,
    step=0.5,
    description="Extra Delivery Cost ($):",
    style={"description_width": "initial"},
    layout=widgets.Layout(width="500px")
)

output = widgets.Output()

# ==========================================
# DASHBOARD UPDATE FUNCTION
# ==========================================

def update_dashboard(change=None):

    with output:
        clear_output(wait=True)

        # ----------------------------------
        # 1. COMMISSION RATE SENSITIVITY
        # ----------------------------------

        commission_change = commission_slider.value / 100

        original_rate = data["CommissionRate"].clip(0, 1)

        new_rate = (
            original_rate + commission_change
        ).clip(0, 1)

        actual_rate_change = new_rate - original_rate

        # Assumption: CommissionRate applies to both platforms
        uber_profit = (
            data["UberEatsNetProfit"]
            - data["UberEatsRevenue"] * actual_rate_change
        )

        doordash_profit = (
            data["DoorDashNetProfit"]
            - data["DoorDashRevenue"] * actual_rate_change
        )

        current_uber_profit = data["UberEatsNetProfit"].sum()
        current_dd_profit = data["DoorDashNetProfit"].sum()

        adjusted_uber_profit = uber_profit.sum()
        adjusted_dd_profit = doordash_profit.sum()

        # ----------------------------------
        # 2. DELIVERY COST SENSITIVITY
        # ----------------------------------

        extra_cost = delivery_slider.value

        total_sd_orders = data["SelfDeliveryOrders"].sum()

        current_sd_profit = data["SelfDeliveryNetProfit"].sum()

        additional_delivery_expense = (
            data["SelfDeliveryOrders"] * extra_cost
        ).sum()

        adjusted_sd_profit = (
            current_sd_profit - additional_delivery_expense
        )

        # ----------------------------------
        # 3. BREAK-EVEN CALCULATION
        # ----------------------------------

        if total_sd_orders > 0:

            breakeven_extra_cost = (
                current_sd_profit / total_sd_orders
            )

            weighted_delivery_cost = (
                (
                    data["DeliveryCostPerOrder"]
                    * data["SelfDeliveryOrders"]
                ).sum() / total_sd_orders
            )

            breakeven_total_cost = (
                weighted_delivery_cost + breakeven_extra_cost
            )

        else:
            breakeven_extra_cost = np.nan
            weighted_delivery_cost = np.nan
            breakeven_total_cost = np.nan

        # ----------------------------------
        # 4. KPI CARDS
        # ----------------------------------

        display(HTML(f"""
        <h3 style='color:#1F4E78;'>Key Performance Indicators</h3>

        <table style='width:100%; text-align:center;'>
        <tr>
        <td style='background:#EAF2F8;padding:15px;'>
        <b>Uber Eats Adjusted Profit</b><br>
        <span style='font-size:22px;'>
        ${adjusted_uber_profit:,.2f}
        </span>
        </td>

        <td style='background:#E8F8F5;padding:15px;'>
        <b>DoorDash Adjusted Profit</b><br>
        <span style='font-size:22px;'>
        ${adjusted_dd_profit:,.2f}
        </span>
        </td>

        <td style='background:#FCF3CF;padding:15px;'>
        <b>Self-Delivery Adjusted Profit</b><br>
        <span style='font-size:22px;'>
        ${adjusted_sd_profit:,.2f}
        </span>
        </td>
        </tr>
        </table>
        """))

        # ----------------------------------
        # 5. COMMISSION SENSITIVITY LINE CHART
        # ----------------------------------

        commission_changes = np.arange(-20, 21, 1)

        uber_sensitivity = []
        dd_sensitivity = []

        for change_pct in commission_changes:

            adjusted_rate = (
                original_rate + change_pct / 100
            ).clip(0, 1)

            rate_difference = adjusted_rate - original_rate

            uber_sensitivity.append(
                (
                    data["UberEatsNetProfit"]
                    - data["UberEatsRevenue"] * rate_difference
                ).sum()
            )

            dd_sensitivity.append(
                (
                    data["DoorDashNetProfit"]
                    - data["DoorDashRevenue"] * rate_difference
                ).sum()
            )

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(
            commission_changes,
            uber_sensitivity,
            label="Uber Eats",
            marker="."
        )

        ax.plot(
            commission_changes,
            dd_sensitivity,
            label="DoorDash",
            marker="."
        )

        ax.axvline(
            commission_slider.value,
            linestyle="--",
            label="Selected Change"
        )

        ax.set_title("Commission Rate Change vs Net Profit")
        ax.set_xlabel("Commission Change (Percentage Points)")
        ax.set_ylabel("Net Profit ($)")
        ax.grid(True, alpha=0.3)
        ax.legend()

        plt.show()
        plt.close(fig)

        # ----------------------------------
        # 6. DELIVERY COST SENSITIVITY
        # ----------------------------------

        cost_increases = np.arange(0, 10.5, 0.5)

        sd_sensitivity = [
            current_sd_profit - total_sd_orders * cost
            for cost in cost_increases
        ]

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(
            cost_increases,
            sd_sensitivity,
            marker="o",
            label="Self-Delivery Net Profit"
        )

        ax.axhline(
            0,
            linestyle="--",
            label="Break-even Profit"
        )

        ax.axvline(
            delivery_slider.value,
            linestyle=":",
            label="Selected Extra Cost"
        )

        ax.set_title("Additional Delivery Cost vs Net Profit")
        ax.set_xlabel("Additional Cost Per Order ($)")
        ax.set_ylabel("Net Profit ($)")
        ax.grid(True, alpha=0.3)
        ax.legend()

        plt.show()
        plt.close(fig)

        # ----------------------------------
        # 7. CURRENT VS ADJUSTED PROFIT
        # ----------------------------------

        profit_comparison = pd.DataFrame({
            "Channel": [
                "Uber Eats",
                "DoorDash",
                "Self-Delivery"
            ],
            "Current Profit": [
                current_uber_profit,
                current_dd_profit,
                current_sd_profit
            ],
            "Adjusted Profit": [
                adjusted_uber_profit,
                adjusted_dd_profit,
                adjusted_sd_profit
            ]
        })

        display(HTML("<h3>Current vs Adjusted Net Profit</h3>"))
        display(profit_comparison.round(2))

        fig, ax = plt.subplots(figsize=(10, 5))

        x = np.arange(len(profit_comparison))
        width = 0.35

        ax.bar(
            x - width / 2,
            profit_comparison["Current Profit"],
            width,
            label="Current Profit"
        )

        ax.bar(
            x + width / 2,
            profit_comparison["Adjusted Profit"],
            width,
            label="Adjusted Profit"
        )

        ax.set_xticks(x)
        ax.set_xticklabels(profit_comparison["Channel"])
        ax.set_ylabel("Net Profit ($)")
        ax.set_title("Channel-Wise Profit Comparison")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        plt.show()
        plt.close(fig)

        # ----------------------------------
        # 8. SELF-DELIVERY BREAK-EVEN
        # ----------------------------------

        display(HTML("<h3>Self-Delivery Break-even Analysis</h3>"))

        if total_sd_orders > 0:

            display(HTML(f"""
            <table style='width:100%; text-align:center;'>
            <tr>
            <td style='background:#EAF2F8;padding:15px;'>
            <b>Current Profit</b><br>
            ${current_sd_profit:,.2f}
            </td>

            <td style='background:#E8F8F5;padding:15px;'>
            <b>Extra Cost at Break-even / Order</b><br>
            ${breakeven_extra_cost:,.2f}
            </td>

            <td style='background:#FCF3CF;padding:15px;'>
            <b>Estimated Total Cost at Break-even / Order</b><br>
            ${breakeven_total_cost:,.2f}
            </td>
            </tr>
            </table>
            """))

            if adjusted_sd_profit > 0:
                print(
                    "Result: Self-Delivery remains profitable "
                    "under the selected cost increase."
                )

            elif np.isclose(adjusted_sd_profit, 0):
                print(
                    "Result: Self-Delivery is at break-even "
                    "under the selected cost increase."
                )

            else:
                print(
                    "Result: Self-Delivery operates at a loss "
                    "under the selected cost increase."
                )

        else:
            print(
                "No Self-Delivery orders found. "
                "Please check the SelfDeliveryOrders column."
            )

        # ----------------------------------
        # 9. SUMMARY
        # ----------------------------------

        display(HTML("""
        <hr>
        <p style='color:#1F4E78;'>
        <b>Analysis Summary:</b> Adjust the sliders above to evaluate
        commission changes, delivery cost increases, and their
        impact on channel profitability.
        </p>
        """))


# ==========================================
# CONNECT SLIDERS TO DASHBOARD
# ==========================================

commission_slider.observe(update_dashboard, names="value")
delivery_slider.observe(update_dashboard, names="value")

display(commission_slider)
display(delivery_slider)
display(output)

# Display dashboard initially
update_dashboard()




# Current vs Adjusted Profit Comparison

import pandas as pd
import matplotlib.pyplot as plt

# Calculate current profit for each channel

in_store_profit = df["InStoreNetProfit"].sum()
uber_eats_profit = df["UberEatsNetProfit"].sum()
door_dash_profit = df["DoorDashNetProfit"].sum()
self_delivery_profit = df["SelfDeliveryNetProfit"].sum()

# Create a table for profit comparison

profit_data = {
    "Channel": [
        "In-Store",
        "Uber Eats",
        "DoorDash",
        "Self-Delivery"
    ],

    "Current Profit": [
        in_store_profit,
        uber_eats_profit,
        door_dash_profit,
        self_delivery_profit
    ]
}

profit_comparison = pd.DataFrame(profit_data)

# Initially, adjusted profit is the same as current profit.
# Replace these values with sensitivity analysis results
# when commission and delivery cost changes are applied.

profit_comparison["Adjusted Profit"] = (
    profit_comparison["Current Profit"]
)

# Calculate the difference in profit

profit_comparison["Profit Change"] = (
    profit_comparison["Adjusted Profit"]
    - profit_comparison["Current Profit"]
)

# Display the comparison table

display(profit_comparison.round(2))

# Create a bar chart

profit_comparison.plot(
    x="Channel",
    y=["Current Profit", "Adjusted Profit"],
    kind="bar",
    figsize=(10, 5),
    width=0.8
)

plt.title("Current vs Adjusted Profit by Channel")
plt.xlabel("Sales Channel")
plt.ylabel("Net Profit ($)")
plt.xticks(rotation=0)
plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.show()




#commission & Delivery cost impact analysis
#Acess sensitivity of net profit to:1) Commission RAte changes. 2)delivery cost order increses
#Indentify breakdown thresholds for self delivery





import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ipywidgets as widgets

from IPython.display import display, clear_output

# ==========================================
# COMMISSION & DELIVERY COST IMPACT ANALYSIS
# ==========================================

data = df.copy()

# Check required columns
required_columns = [
    "CommissionRate",
    "DeliveryCostPerOrder",
    "InStoreNetProfit",
    "UberEatsOrders",
    "DoorDashOrders",
    "SelfDeliveryOrders",
    "InStoreRevenue",
    "UberEatsRevenue",
    "DoorDashRevenue",
    "InStoreNetProfit",
    "UberEatsNetProfit",
    "DoorDashNetProfit",
    "SelfDeliveryNetProfit"
]

missing_columns = [
    col for col in required_columns if col not in data.columns
]

if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")

# Convert columns to numeric
for col in required_columns:
    data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0)


# ==========================================
# DASHBOARD TITLE
# ==========================================

print("=" * 55)
print(" COMMISSION & DELIVERY COST IMPACT ANALYSIS")
print(" Restaurant Profitability Dashboard")
print("=" * 55)


# ==========================================
# CREATE SLIDERS
# ==========================================

commission_slider = widgets.IntSlider(
    value=0,
    min=-20,
    max=20,
    step=1,
    description="Commission Change (% points):",
    style={"description_width": "initial"},
    layout=widgets.Layout(width="550px")
)

delivery_slider = widgets.FloatSlider(
    value=0,
    min=0,
    max=10,
    step=0.5,
    description="Extra Delivery Cost ($):",
    style={"description_width": "initial"},
    layout=widgets.Layout(width="550px")
)

output = widgets.Output()


# ==========================================
# DASHBOARD UPDATE FUNCTION
# ==========================================

def update_dashboard(change=None):

    with output:
        clear_output(wait=True)

        # ----------------------------------
        # 1. CURRENT PROFIT
        # ----------------------------------

        current_instore_profit = data["InStoreNetProfit"].sum()
        current_uber_profit = data["UberEatsNetProfit"].sum()
        current_dd_profit = data["DoorDashNetProfit"].sum()
        current_sd_profit = data["SelfDeliveryNetProfit"].sum()

        # ----------------------------------
        # 2. COMMISSION IMPACT
        # ----------------------------------

        commission_change = commission_slider.value / 100

        original_rate = data["CommissionRate"].clip(0, 1)

        new_rate = (
            original_rate + commission_change
        ).clip(0, 1)

        rate_difference = new_rate - original_rate

        adjusted_uber_profit = (
            data["UberEatsNetProfit"]
            - data["UberEatsRevenue"] * rate_difference
        ).sum()

        adjusted_dd_profit = (
            data["DoorDashNetProfit"]
            - data["DoorDashRevenue"] * rate_difference
        ).sum()

        # ----------------------------------
        # 3. SELF-DELIVERY COST IMPACT
        # ----------------------------------

        extra_cost = delivery_slider.value

        total_sd_orders = data["SelfDeliveryOrders"].sum()

        extra_delivery_expense = (
            data["SelfDeliveryOrders"] * extra_cost
        ).sum()

        adjusted_sd_profit = (
            current_sd_profit - extra_delivery_expense
        )

        # In-Store profit remains unchanged
        adjusted_instore_profit = current_instore_profit

        # ----------------------------------
        # 4. KPI CARDS
        # ----------------------------------

        print("\nKEY PERFORMANCE INDICATORS")
        print("-" * 55)

        kpi_data = pd.DataFrame({
            "Channel": [
                "In-Store",
                "Uber Eats",
                "DoorDash",
                "Self-Delivery"
            ],
            "Adjusted Profit ($)": [
                adjusted_instore_profit,
                adjusted_uber_profit,
                adjusted_dd_profit,
                adjusted_sd_profit
            ]
        })

        display(kpi_data.round(2))

        # ----------------------------------
        # 5. COMMISSION SENSITIVITY LINE CHART
        # ----------------------------------

        commission_changes = np.arange(-20, 21, 1)

        uber_sensitivity = []
        dd_sensitivity = []

        for change_pct in commission_changes:

            changed_rate = (
                original_rate + change_pct / 100
            ).clip(0, 1)

            rate_difference = changed_rate - original_rate

            uber_profit = (
                data["UberEatsNetProfit"]
                - data["UberEatsRevenue"] * rate_difference
            ).sum()

            dd_profit = (
                data["DoorDashNetProfit"]
                - data["DoorDashRevenue"] * rate_difference
            ).sum()

            uber_sensitivity.append(uber_profit)
            dd_sensitivity.append(dd_profit)

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(
            commission_changes,
            uber_sensitivity,
            label="Uber Eats",
            marker="."
        )

        ax.plot(
            commission_changes,
            dd_sensitivity,
            label="DoorDash",
            marker="."
        )

        ax.axvline(
            commission_slider.value,
            linestyle="--",
            label="Selected Change"
        )

        ax.set_title("Commission Change vs Net Profit")
        ax.set_xlabel("Commission Change (Percentage Points)")
        ax.set_ylabel("Net Profit ($)")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()
        plt.close(fig)

        # ----------------------------------
        # 6. DELIVERY COST SENSITIVITY
        # ----------------------------------

        cost_increases = np.arange(0, 10.5, 0.5)

        sd_sensitivity = [
            current_sd_profit - total_sd_orders * cost
            for cost in cost_increases
        ]

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(
            cost_increases,
            sd_sensitivity,
            marker="o",
            label="Self-Delivery Profit"
        )

        ax.axhline(
            0,
            linestyle="--",
            label="Break-even Profit"
        )

        ax.axvline(
            delivery_slider.value,
            linestyle=":",
            label="Selected Extra Cost"
        )

        ax.set_title("Extra Delivery Cost vs Net Profit")
        ax.set_xlabel("Additional Cost Per Order ($)")
        ax.set_ylabel("Net Profit ($)")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()
        plt.close(fig)

        # ----------------------------------
        # 7. FOUR-CHANNEL PROFIT COMPARISON
        # ----------------------------------

        profit_comparison = pd.DataFrame({
            "Channel": [
                "In-Store",
                "Uber Eats",
                "DoorDash",
                "Self-Delivery"
            ],
            "Current Profit": [
                current_instore_profit,
                current_uber_profit,
                current_dd_profit,
                current_sd_profit
            ],
            "Adjusted Profit": [
                adjusted_instore_profit,
                adjusted_uber_profit,
                adjusted_dd_profit,
                adjusted_sd_profit
            ]
        })

        profit_comparison["Profit Change"] = (
            profit_comparison["Adjusted Profit"]
            - profit_comparison["Current Profit"]
        )

        print("\nFOUR-CHANNEL PROFITABILITY COMPARISON")
        print("-" * 55)

        display(profit_comparison.round(2))

        # Bar chart
        fig, ax = plt.subplots(figsize=(10, 5))

        x = np.arange(len(profit_comparison))
        width = 0.35

        ax.bar(
            x - width / 2,
            profit_comparison["Current Profit"],
            width,
            label="Current Profit"
        )

        ax.bar(
            x + width / 2,
            profit_comparison["Adjusted Profit"],
            width,
            label="Adjusted Profit"
        )

        ax.set_xticks(x)
        ax.set_xticklabels(profit_comparison["Channel"])

        ax.set_title("Current vs Adjusted Profit by Channel")
        ax.set_xlabel("Sales Channel")
        ax.set_ylabel("Net Profit ($)")

        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()
        plt.show()
        plt.close(fig)

        # ----------------------------------
        # 8. SELF-DELIVERY BREAK-EVEN
        # ----------------------------------

        print("\nSELF-DELIVERY BREAK-EVEN ANALYSIS")
        print("-" * 55)

        if total_sd_orders > 0:

            breakeven_extra_cost = (
                current_sd_profit / total_sd_orders
            )

            breakeven_data = pd.DataFrame({
                "Metric": [
                    "Current Self-Delivery Profit ($)",
                    "Break-even Extra Cost Per Order ($)",
                    "Selected Extra Cost Per Order ($)",
                    "Adjusted Self-Delivery Profit ($)"
                ],
                "Value": [
                    current_sd_profit,
                    breakeven_extra_cost,
                    extra_cost,
                    adjusted_sd_profit
                ]
            })

            display(breakeven_data.round(2))

            if adjusted_sd_profit > 0:
                print("Result: Self-Delivery is profitable.")

            elif np.isclose(adjusted_sd_profit, 0):
                print("Result: Self-Delivery is at break-even.")

            else:
                print("Result: Self-Delivery is operating at a loss.")

        else:
            print("No Self-Delivery orders found. Check the dataset.")

        # ----------------------------------
        # 9. SUMMARY
        # ----------------------------------

        print("\nANALYSIS SUMMARY")
        print("-" * 55)
        print("Adjust the sliders to see changes in profitability.")
        print("In-Store profit remains unchanged in this scenario.")
        print("Uber Eats and DoorDash respond to commission changes.")
        print("Self-Delivery responds to additional delivery costs.")


# ==========================================
# CONNECT SLIDERS
# ==========================================

commission_slider.observe(update_dashboard, names="value")
delivery_slider.observe(update_dashboard, names="value")

display(commission_slider)
display(delivery_slider)
display(output)

# Display dashboard initially
update_dashboard()


# Current vs Adjusted Profit Comparison

import pandas as pd
import matplotlib.pyplot as plt

# Calculate current profit for each channel

in_store_profit = df["InStoreNetProfit"].sum()
uber_eats_profit = df["UberEatsNetProfit"].sum()
door_dash_profit = df["DoorDashNetProfit"].sum()
self_delivery_profit = df["SelfDeliveryNetProfit"].sum()

# Create a table for profit comparison

profit_data = {
    "Channel": [
        "In-Store",
        "Uber Eats",
        "DoorDash",
        "Self-Delivery"
    ],

    "Current Profit": [
        in_store_profit,
        uber_eats_profit,
        door_dash_profit,
        self_delivery_profit
    ]
}

profit_comparison = pd.DataFrame(profit_data)

# Initially, adjusted profit is the same as current profit.
# Replace these values with sensitivity analysis results
# when commission and delivery cost changes are applied.

profit_comparison["Adjusted Profit"] = (
    profit_comparison["Current Profit"]
)

# Calculate the difference in profit

profit_comparison["Profit Change"] = (
    profit_comparison["Adjusted Profit"]
    - profit_comparison["Current Profit"]
)

# Display the comparison table

display(profit_comparison.round(2))

# Create a bar chart

profit_comparison.plot(
    x="Channel",
    y=["Current Profit", "Adjusted Profit"],
    kind="bar",
    figsize=(10, 5),
    width=0.8
)

plt.title("Current vs Adjusted Profit by Channel")
plt.xlabel("Sales Channel")
plt.ylabel("Net Profit ($)")
plt.xticks(rotation=0)
plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.show()



#commission & Delivery cost impact analysis
#Acess sensitivity of net profit to:1) Commission RAte changes. 2)delivery cost order increses
#Indentify breakdown thresholds for self delivery





import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ipywidgets as widgets

from IPython.display import display, clear_output

# ==========================================
# COMMISSION & DELIVERY COST IMPACT ANALYSIS
# ==========================================

data = df.copy()

# Check required columns
required_columns = [
    "CommissionRate",
    "DeliveryCostPerOrder",
    "InStoreNetProfit",
    "UberEatsOrders",
    "DoorDashOrders",
    "SelfDeliveryOrders",
    "InStoreRevenue",
    "UberEatsRevenue",
    "DoorDashRevenue",
    "InStoreNetProfit",
    "UberEatsNetProfit",
    "DoorDashNetProfit",
    "SelfDeliveryNetProfit"
]

missing_columns = [
    col for col in required_columns if col not in data.columns
]

if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")

# Convert columns to numeric
for col in required_columns:
    data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0)


# ==========================================
# DASHBOARD TITLE
# ==========================================

print("=" * 55)
print(" COMMISSION & DELIVERY COST IMPACT ANALYSIS")
print(" Restaurant Profitability Dashboard")
print("=" * 55)


# ==========================================
# CREATE SLIDERS
# ==========================================

commission_slider = widgets.IntSlider(
    value=0,
    min=-20,
    max=20,
    step=1,
    description="Commission Change (% points):",
    style={"description_width": "initial"},
    layout=widgets.Layout(width="550px")
)

delivery_slider = widgets.FloatSlider(
    value=0,
    min=0,
    max=10,
    step=0.5,
    description="Extra Delivery Cost ($):",
    style={"description_width": "initial"},
    layout=widgets.Layout(width="550px")
)

output = widgets.Output()


# ==========================================
# DASHBOARD UPDATE FUNCTION
# ==========================================

def update_dashboard(change=None):

    with output:
        clear_output(wait=True)

        # ----------------------------------
        # 1. CURRENT PROFIT
        # ----------------------------------

        current_instore_profit = data["InStoreNetProfit"].sum()
        current_uber_profit = data["UberEatsNetProfit"].sum()
        current_dd_profit = data["DoorDashNetProfit"].sum()
        current_sd_profit = data["SelfDeliveryNetProfit"].sum()

        # ----------------------------------
        # 2. COMMISSION IMPACT
        # ----------------------------------

        commission_change = commission_slider.value / 100

        original_rate = data["CommissionRate"].clip(0, 1)

        new_rate = (
            original_rate + commission_change
        ).clip(0, 1)

        rate_difference = new_rate - original_rate

        adjusted_uber_profit = (
            data["UberEatsNetProfit"]
            - data["UberEatsRevenue"] * rate_difference
        ).sum()

        adjusted_dd_profit = (
            data["DoorDashNetProfit"]
            - data["DoorDashRevenue"] * rate_difference
        ).sum()

        # ----------------------------------
        # 3. SELF-DELIVERY COST IMPACT
        # ----------------------------------

        extra_cost = delivery_slider.value

        total_sd_orders = data["SelfDeliveryOrders"].sum()

        extra_delivery_expense = (
            data["SelfDeliveryOrders"] * extra_cost
        ).sum()

        adjusted_sd_profit = (
            current_sd_profit - extra_delivery_expense
        )

        # In-Store profit remains unchanged
        adjusted_instore_profit = current_instore_profit

        # ----------------------------------
        # 4. KPI CARDS
        # ----------------------------------

        print("\nKEY PERFORMANCE INDICATORS")
        print("-" * 55)

        kpi_data = pd.DataFrame({
            "Channel": [
                "In-Store",
                "Uber Eats",
                "DoorDash",
                "Self-Delivery"
            ],
            "Adjusted Profit ($)": [
                adjusted_instore_profit,
                adjusted_uber_profit,
                adjusted_dd_profit,
                adjusted_sd_profit
            ]
        })

        display(kpi_data.round(2))

        # ----------------------------------
        # 5. COMMISSION SENSITIVITY LINE CHART
        # ----------------------------------

        commission_changes = np.arange(-20, 21, 1)

        uber_sensitivity = []
        dd_sensitivity = []

        for change_pct in commission_changes:

            changed_rate = (
                original_rate + change_pct / 100
            ).clip(0, 1)

            rate_difference = changed_rate - original_rate

            uber_profit = (
                data["UberEatsNetProfit"]
                - data["UberEatsRevenue"] * rate_difference
            ).sum()

            dd_profit = (
                data["DoorDashNetProfit"]
                - data["DoorDashRevenue"] * rate_difference
            ).sum()

            uber_sensitivity.append(uber_profit)
            dd_sensitivity.append(dd_profit)

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(
            commission_changes,
            uber_sensitivity,
            label="Uber Eats",
            marker="."
        )

        ax.plot(
            commission_changes,
            dd_sensitivity,
            label="DoorDash",
            marker="."
        )

        ax.axvline(
            commission_slider.value,
            linestyle="--",
            label="Selected Change"
        )

        ax.set_title("Commission Change vs Net Profit")
        ax.set_xlabel("Commission Change (Percentage Points)")
        ax.set_ylabel("Net Profit ($)")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()
        plt.close(fig)

        # ----------------------------------
        # 6. DELIVERY COST SENSITIVITY
        # ----------------------------------

        cost_increases = np.arange(0, 10.5, 0.5)

        sd_sensitivity = [
            current_sd_profit - total_sd_orders * cost
            for cost in cost_increases
        ]

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(
            cost_increases,
            sd_sensitivity,
            marker="o",
            label="Self-Delivery Profit"
        )

        ax.axhline(
            0,
            linestyle="--",
            label="Break-even Profit"
        )

        ax.axvline(
            delivery_slider.value,
            linestyle=":",
            label="Selected Extra Cost"
        )

        ax.set_title("Extra Delivery Cost vs Net Profit")
        ax.set_xlabel("Additional Cost Per Order ($)")
        ax.set_ylabel("Net Profit ($)")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()
        plt.close(fig)

        # ----------------------------------
        # 7. FOUR-CHANNEL PROFIT COMPARISON
        # ----------------------------------

        profit_comparison = pd.DataFrame({
            "Channel": [
                "In-Store",
                "Uber Eats",
                "DoorDash",
                "Self-Delivery"
            ],
            "Current Profit": [
                current_instore_profit,
                current_uber_profit,
                current_dd_profit,
                current_sd_profit
            ],
            "Adjusted Profit": [
                adjusted_instore_profit,
                adjusted_uber_profit,
                adjusted_dd_profit,
                adjusted_sd_profit
            ]
        })

        profit_comparison["Profit Change"] = (
            profit_comparison["Adjusted Profit"]
            - profit_comparison["Current Profit"]
        )

        print("\nFOUR-CHANNEL PROFITABILITY COMPARISON")
        print("-" * 55)

        display(profit_comparison.round(2))

        # Bar chart
        fig, ax = plt.subplots(figsize=(10, 5))

        x = np.arange(len(profit_comparison))
        width = 0.35

        ax.bar(
            x - width / 2,
            profit_comparison["Current Profit"],
            width,
            label="Current Profit"
        )

        ax.bar(
            x + width / 2,
            profit_comparison["Adjusted Profit"],
            width,
            label="Adjusted Profit"
        )

        ax.set_xticks(x)
        ax.set_xticklabels(profit_comparison["Channel"])

        ax.set_title("Current vs Adjusted Profit by Channel")
        ax.set_xlabel("Sales Channel")
        ax.set_ylabel("Net Profit ($)")

        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()
        plt.show()
        plt.close(fig)

        # ----------------------------------
        # 8. SELF-DELIVERY BREAK-EVEN
        # ----------------------------------

        print("\nSELF-DELIVERY BREAK-EVEN ANALYSIS")
        print("-" * 55)

        if total_sd_orders > 0:

            breakeven_extra_cost = (
                current_sd_profit / total_sd_orders
            )

            breakeven_data = pd.DataFrame({
                "Metric": [
                    "Current Self-Delivery Profit ($)",
                    "Break-even Extra Cost Per Order ($)",
                    "Selected Extra Cost Per Order ($)",
                    "Adjusted Self-Delivery Profit ($)"
                ],
                "Value": [
                    current_sd_profit,
                    breakeven_extra_cost,
                    extra_cost,
                    adjusted_sd_profit
                ]
            })

            display(breakeven_data.round(2))

            if adjusted_sd_profit > 0:
                print("Result: Self-Delivery is profitable.")

            elif np.isclose(adjusted_sd_profit, 0):
                print("Result: Self-Delivery is at break-even.")

            else:
                print("Result: Self-Delivery is operating at a loss.")

        else:
            print("No Self-Delivery orders found. Check the dataset.")

        # ----------------------------------
        # 9. SUMMARY
        # ----------------------------------

        print("\nANALYSIS SUMMARY")
        print("-" * 55)
        print("Adjust the sliders to see changes in profitability.")
        print("In-Store profit remains unchanged in this scenario.")
        print("Uber Eats and DoorDash respond to commission changes.")
        print("Self-Delivery responds to additional delivery costs.")


# ==========================================
# CONNECT SLIDERS
# ==========================================

commission_slider.observe(update_dashboard, names="value")
delivery_slider.observe(update_dashboard, names="value")

display(commission_slider)
display(delivery_slider)
display(output)

# Display dashboard initially
update_dashboard()















