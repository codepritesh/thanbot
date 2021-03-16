from pprint import pprint
from binance.client import Client
from binance.websockets import BinanceSocketManager
from pprint import pprint
import time
import json
import math



class RealtimeData:
    def __init__(self, bot_name,conn_key):

         self._bot_name = bot_name
         self._symbolname = "BTCUSDT"
         self._conn_key = conn_key
         self._sbt_best_bid_price =""
         self._sbt_best_bid_qty =""
         self._sbt_best_ask_price =""
         self._sbt_best_ask_qty =""
         self._st_last_price =""
         self._st_last_qty =""
         self._smp_mark_price =""
         self._smp_index_price =""
         self._entry_price ="0"
         self._growth=[]
         self._lastprice_diffrence= 50.0  #---------------------set price diffrence here
         self._quantity= 0.001 #---------------------set quantity here


    def set_book_Ticker(self,data):
        self._sbt_best_bid_price = data['b']
        self._sbt_best_bid_qty = data['B']
        self._sbt_best_ask_price = data['a']
        self._sbt_best_ask_qty = data['A']

    def set_ticker(self,tickerdata):
        self._st_last_price = tickerdata['c']
        self._st_last_qty = tickerdata['Q']

    def set_markPrice(self,markPriceData):
        self._smp_mark_price = markPriceData['p']
        self._smp_index_price = markPriceData['i']
  
        



api_key= "dej6e3dScRfB6fW9dEsPrE1IcsowqsIw7meEVNIoBk1c7ZIOvtKoSCcQGVCMy8qV"
api_secret = "phi4H9O3msfoSspB0Esxm1uX1Q9bcXZn5Yjit4lgGY0ddCrffo3hzEwO68eXcJV8"

client = Client(api_key, api_secret)

#-------------------------------------------------------------this part will capture data from socket
bm = BinanceSocketManager(client, user_timeout=60)

# start any sockets here, i.e a trade socket
def process_message(msg):
    print(json.dumps(msg, indent=4, sort_keys=True))   

    if msg["stream"] == "btcusdt@bookTicker":
        objdata.set_book_Ticker(msg["data"])

    elif msg["stream"] =="btcusdt@ticker":
        objdata.set_ticker(msg["data"])

    elif msg["stream"] =="btcusdt@ticker":
        objdata.set_ticker(msg["data"])
    else:
         objdata.set_markPrice(msg["data"])   
         

conn_key = bm.start_multiplex_socket_future([ 'btcusdt@bookTicker','btcusdt@ticker','btcusdt@markPrice@1s',], process_message)
#conn_key = bm.start_multiplex_socket(['btcusdt@markPrice@1s','btcusdt@bookTicker'], process_message)
print("conn_key------------",conn_key)
objdata = RealtimeData("Than", conn_key)
##-------------------------------------------------------------this part will capture data from socket
# then start the socket manager
bm.start()
#--------------------------------------------------------------sleep is for socket connection 10 second
time.sleep(5) 
while True:


    print("---_bot_name--------------",objdata._bot_name)
    print("---_conn_key--------------",objdata._conn_key)
    print("---_sbt_best_bid_price----",objdata._sbt_best_bid_price)
    print("---_sbt_best_bid_qty------",objdata._sbt_best_bid_qty)
    print("---_sbt_best_ask_price----",objdata._sbt_best_ask_price)

    print("---_sbt_best_ask_qty------",objdata._sbt_best_ask_qty)
    print("---_st_last_price---------",objdata._st_last_price)
    print("---_st_last_qty-----------",objdata._st_last_qty)
    print("---_smp_mark_price--------",objdata._smp_mark_price)
    print("---_smp_index_price-------",objdata._smp_index_price)

    if objdata._entry_price =="0":
        objdata._entry_price = objdata._st_last_price
        #wait 4 second to load price deference data to calculate wheather price goes up or down.
        time.sleep(4)

    if (float(objdata._entry_price)<float(objdata._st_last_price)): #-----------------this condition to chek growth or fall of price
        print("create open longcontract and store orderid")

        orderinfo = client.futures_create_order(symbol='BTCUSDT', side= client.SIDE_BUY, positionSide="LONG",type= client.ORDER_TYPE_LIMIT, quantity=objdata._quantity,timeInForce= client.TIME_IN_FORCE_GTC, price = (float(objdata._sbt_best_bid_price)))
        print("orderinfo--------",orderinfo)
        orderid = orderinfo["orderId"]
        tenp_liqudprice = (float(orderinfo["price"]) * float(orderinfo["origQty"])) * 0.1
        cutlose_sell_price = (float(orderinfo["price"]) * float(orderinfo["origQty"])) -  tenp_liqudprice
        # check order fill status
        while True :

            order_status = client.futures_get_order(symbol="BTCUSDT", orderId= int(orderid))
            result_status = orderstatus["status"]



            if ((result_status == "NEW") or (result_status == "PARTIALLY_FILLED")):
                time.sleep(1)
                continue


            elif(result_status == "FILLED"):

                while float(objdata._st_last_price) < (float(objdata._entry_price)+objdata._lastprice_diffrence):
                    print("checking price growth")
                    print(objdata._st_last_price,(float(objdata._entry_price)+ objdata._lastprice_diffrence))
                    #if value downgraded below 10% of Liquidation Price - Entry Price.
                    if (float(objdata._st_last_price) * float(orderinfo["origQty"]))  <= cutlose_sell_price:
                        orderinfo = client.futures_create_order(symbol='BTCUSDT', side= client.SIDE_SELL, positionSide="LONG",type= client.ORDER_TYPE_LIMIT, quantity=objdata._quantity,timeInForce= client.TIME_IN_FORCE_GTC, price = float(objdata._st_last_price))
                        break
                if float(objdata._st_last_price) >= (float(objdata._entry_price)+ objdata._lastprice_diffrence):
                    print("--------------------------------pricewent up--create order take profit on long_contract")
                    orderinfo = client.futures_create_order(symbol='BTCUSDT', side= client.SIDE_SELL, positionSide="LONG",type= client.ORDER_TYPE_LIMIT, quantity=objdata._quantity,timeInForce= client.TIME_IN_FORCE_GTC, price = float(objdata._st_last_price))
                    print(objdata._st_last_price,(float(objdata._entry_price)+ objdata._lastprice_diffrence))

                else:
                    break
            else:
                break


        
    else:

        orderinfo = client.futures_create_order(symbol='BTCUSDT', side= client.SIDE_BUY, positionSide="SHORT",type= client.ORDER_TYPE_LIMIT, quantity=objdata._quantity,timeInForce= client.TIME_IN_FORCE_GTC, price = (float(objdata._sbt_best_bid_price)))
        print("orderinfo--------",orderinfo)
        orderid = orderinfo["orderId"]
        tenp_liqudprice = (float(orderinfo["price"]) * float(orderinfo["origQty"])) * 0.1
        cutlose_sell_price = (float(orderinfo["price"]) * float(orderinfo["origQty"])) +  tenp_liqudprice
        # check order fill status
        while True :

            order_status = client.futures_get_order(symbol="BTCUSDT", orderId = int(orderid))
            result_status = orderstatus["status"]



            if ((result_status == "NEW") or (result_status == "PARTIALLY_FILLED")):
                time.sleep(1)
                continue


            elif(result_status == "FILLED"):

                while float(objdata._st_last_price) > (float(objdata._entry_price)-objdata._lastprice_diffrence):
                    print("checking price Fall")
                    print(objdata._st_last_price,(float(objdata._entry_price)-objdata._lastprice_diffrence))
                    #if value downgraded below 10% of Liquidation Price - Entry Price.
                    if (float(objdata._st_last_price) * float(orderinfo["origQty"]))  >= cutlose_sell_price:
                        orderinfo = client.futures_create_order(symbol='BTCUSDT', side= client.SIDE_SELL, positionSide="SHORT",type= client.ORDER_TYPE_LIMIT, quantity=objdata._quantity,timeInForce= client.TIME_IN_FORCE_GTC, price = float(objdata._st_last_price))
                        break
                if float(objdata._st_last_price) <= (float(objdata._entry_price) - objdata._lastprice_diffrence):
                    print("--------------------------------price fell - create order take profit on short_contract")
                    orderinfo = client.futures_create_order(symbol='BTCUSDT', side= client.SIDE_SELL, positionSide="SHORT",type= client.ORDER_TYPE_LIMIT, quantity=objdata._quantity,timeInForce= client.TIME_IN_FORCE_GTC, price = float(objdata._st_last_price))
                    print(objdata._st_last_price,(float(objdata._entry_price)+ objdata._lastprice_diffrence))

                else:
                    break
            else:
                break



    objdata._entry_price = objdata._st_last_price
    print("entryprice set----------- ------------------------------------------------entryprice set")
    time.sleep(1)





