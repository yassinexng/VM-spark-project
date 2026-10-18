import requests, json
import  numpy as np
import pandas as pd

def get_coins_asjson():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"

    r = requests.get(url)
    r.raise_for_status()
    jsoned_r = r.json()
    print(json.dumps(jsoned_r, indent=2))
    l = len(jsoned_r)
    print(l)

    roi = {
        'times': None,
        'currency': None,
        'percentage': None
    }

    rows = {
        "symbol": "ticket_symbol",
        "current_price": "live_price_usd",
        "total_volume": "24_hour_trading_volume",
        "market_cap_rank": "market_cap_rank",
        "high_24h": "highest_last24h",
        "low_24h": "lowest_last24h",
        "ath": "all_times_high_price",
        "ath_date": "when_all_times_occured_1",
        "roi": roi,
        "last_updated": "data_snapshot_date"
    }

    values = [
        {

        } for _ in range(l)
        ]

    for i in range(l):
        for key, value in rows.items():
            if key == "roi":
                values[i]["roi"] = {}
                for k in roi.keys():
                    if jsoned_r[i]["roi"] is None:
                        values[i]["roi"][k] = None
                    else:
                        values[i]["roi"][k] = jsoned_r[i]["roi"][k]
            else:
                values[i][rows[key]] = jsoned_r[i][key]
        p = ""
        values[i]["data_snapshot__date"], p = values[i]["data_snapshot_date"].split("T")
        del values[i]["data_snapshot_date"]
        s = ""
        values[i]["when_all_times_occured"],s = values[i][ "when_all_times_occured_1"].split("T")
        del values[i][ "when_all_times_occured_1"]

    return values


def generate_more():
    row_count = 1000000
    values = get_coins_asjson()
    topic1 = [
        "ticket_symbol", "live_price_usd", "24_hour_trading_volume", "highest_last24h", "lowest_last24h","data_snapshot__date"
    ]
    topic2 = [
        "times", "currency", "percentage"
    ]
    topic3 = [
        "all_times_high_price", "when_all_times_occured", "market_cap_rank"
    ]

    topic1_data = {}
    topic2_data = {}
    topic3_data = {}

    for item in values:
        for k,v in item.items():
            if k in topic1:
                if k in topic1_data:
                    topic1_data[k].append(v)
                else:
                    topic1_data[k] = [v]
            elif k == "roi":
                for l, j in v.items():
                    if l in topic2_data:
                        topic2_data[l].append(j)
                    else:
                        topic2_data[l] = [j]
            if k in topic3:
                if k in topic3_data:
                    topic3_data[k].append(v)
                else:
                    topic3_data[k] = [v]
    
    df1 = pd.DataFrame(topic1_data)
    df2 = pd.DataFrame(topic2_data)
    df3 = pd.DataFrame(topic3_data)


   
    new_symbols = np.random.choice(df1["ticket_symbol"].unique(),row_count)
    new_live_prices = np.random.uniform(df1["live_price_usd"].min(), df1["live_price_usd"].max(), row_count)
    new_24h_trading_volumes = np.random.uniform(df1["24_hour_trading_volume"].min(), df1["24_hour_trading_volume"].max(),row_count)
    new_highest_24h, new_lowest_24h = np.random.uniform(df1["highest_last24h"].min(), df1["highest_last24h"].max() ,row_count), np.random.uniform(df1["lowest_last24h"].min(), df1["lowest_last24h"].max(),row_count)
    new_dates = pd.date_range(pd.to_datetime(df1["data_snapshot__date"].max()).date(), periods=row_count, freq="MS")   

    df1_randomized = pd.DataFrame({
        "ticket_symbol": new_symbols,
        "live_price_usd": new_live_prices,
        "24_hour_trading_volume": new_24h_trading_volumes,
        "highest_last24h": new_highest_24h,
        "lowest_last24h": new_lowest_24h,
        "data_snapshot__date": new_dates
    })

    new_times = np.random.uniform(df2["times"].min(), df2["times"].max(), row_count)
    new_currencies = np.random.choice(df2["currency"].dropna().unique(), row_count)
    new_percentages = np.random.uniform(df2["percentage"].min(), df2["percentage"].max(), row_count)

    df2_randomized = pd.DataFrame({
        "times": new_times,
        "currency": new_currencies,
        "percentage": new_percentages
    })

    new_ath = np.random.uniform(df3["all_times_high_price"].min(), df3["all_times_high_price"].max(), row_count)
    new_ath_dates = np.random.choice(df3["when_all_times_occured"].unique(), row_count)
    new_ranks = np.random.randint(df3["market_cap_rank"].min(), df3["market_cap_rank"].max() + 1, row_count)

    df3_randomized = pd.DataFrame({
        "all_times_high_price": new_ath,
        "when_all_times_occured": new_ath_dates,
        "market_cap_rank": new_ranks
    })

    return df1_randomized, df2_randomized, df3_randomized   


def show(v):
    print("\n"*5)
    print(v)




if __name__ == "__main__":
    df1,df2,df3 = generate_more()
    show(df1.info())
    show(df2.info())
    show(df3.info())
   