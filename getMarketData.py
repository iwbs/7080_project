import futu as ft
import const


# get HSI with futu api
quote_ctx = ft.OpenQuoteContext(host="127.0.0.1", port=11111)
quote_ctx.start()
quote_ctx.set_handler(ft.TickerHandlerBase())
ret, df, key = quote_ctx.request_history_kline(const.HSIF_SPOT_CODE, start=const.RQ_START_DATE, end=const.RQ_END_DATE, max_count=None)
ret_next, df_next, key_next = quote_ctx.request_history_kline(const.HSIF_NEXT_CODE, start=const.RQ_START_DATE, end=const.RQ_END_DATE, max_count=None)
# market = ft.Market.HK
# print(quote_ctx.get_stock_basicinfo(market, stock_type=ft.SecurityType.IDX))
quote_ctx.stop()
quote_ctx.close()

df.to_csv('hsi_spot.csv')
df_next.to_csv('hsi_next.csv')