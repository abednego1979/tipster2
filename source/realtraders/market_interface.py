#*- coding: utf-8 -*-
#Python 3.5.x
#utf8编码

#本文件用于封装各个市场的交易API接口

#目前使用的是中信建投的服务

#真实交易者的基类
class traderBase():
    def __init__(self, market, info={}):
        #基本的交易者信息：操作的对象市场，以及这个市场相应的初始化数据，如访问key
        pass
    #"获取账号详情"
    def getAccountInfo(self):
        pass
    #"获取所有正在进行的委托
    def getOrders(self, coinType):
        pass
    #"获取订单详情"
    def getOrderInfo(self, coinType,id,):
        pass
    #"限价买入"
    def buy(self, coinType,price,amount,tradePassword,tradeid):
        pass
    #"限价卖出"
    def sell(self, coinType,price,amount,tradePassword,tradeid):
        pass
    #"市价买入"
    def buyMarket(self, coinType,amount,tradePassword,tradeid):
        pass    
    #"市价卖出"
    def sellMarket(self, coinType,amount,tradePassword,tradeid):
        pass
    #"查询个人最新10条成交订单"
    def getNewDealOrders(self, coinType):
        pass
    #"根据trade_id查询order_id"
    def getOrderIdByTradeId(self, coinType,tradeid):
        pass    
    #"取消订单接口"
    def cancelOrder(self, coinType,id):
        pass

#huobi_btc_cny的真实交易类
class trader_huobi_btc_cny(traderBase):
    def __init__(self):
        
        super(trader_huobi_btc_cny, self).__init__()
        pass
    
    #"获取账号详情"
    def getAccountInfo(self):
        HuobiService.getAccountInfo(HuobiUtil.ACCOUNT_INFO)
    #"获取所有正在进行的委托
    #coinType:币种 1 比特币 2 莱特币
    def getOrders(self, coinType):
        HuobiService.getOrders(coinType, HuobiUtil.GET_ORDERS)
    #"获取订单详情"
    #coinType:币种 1 比特币 2 莱特币
    #orderId:委托订单ID
    def getOrderInfo(self, coinType, orderId):
        HuobiService.getOrderInfo(coinType, orderId, HuobiUtil.ORDER_INFO)
        pass
    #"限价买入"
    #coinType:币种 1 比特币 2 莱特币
    #price:买入价格
    #amount:买入数量
    #tradePassword:如果开启下单时输入资金密码，必须传此参数,此项不参与sign签名过程
    #tradeid:用户自定义订单号为数字(最多15位，唯一值),此项不参与sign签名过程
    def buy(self, coinType, price, amount, tradePassword, tradeid):
        HuobiService.buy(coinType, price, amount, tradePassword, tradeid, HuobiUtil.BUY)
        pass
    #"限价卖出"
    #coinType:币种 1 比特币 2 莱特币
    #price:卖出价格
    #amount:卖出数量
    #tradePassword:如果开启下单时输入资金密码，必须传此参数,此项不参与sign签名过程
    #tradeid:用户自定义订单号为数字(最多15位，唯一值),此项不参与sign签名过程
    def sell(self, coinType, price, amount, tradePassword, tradeid):
        HuobiService.sell(coinType, price, amount, tradePassword, tradeid, HuobiUtil.SELL)
        pass
    #"市价买入"
    #coinType:币种 1 比特币 2 莱特币
    #amount:买入数量
    #tradePassword:如果开启下单时输入资金密码，必须传此参数,此项不参与sign签名过程
    #tradeid:用户自定义订单号为数字(最多15位，唯一值),此项不参与sign签名过程
    def buyMarket(self, coinType, amount, tradePassword, tradeid):
        HuobiService.buyMarket(coinType, amount, tradePassword, tradeid, HuobiUtil.BUY_MARKET)
        pass    
    #"市价卖出"
    #coinType:币种 1 比特币 2 莱特币
    #amount:卖出数量
    #tradePassword:如果开启下单时输入资金密码，必须传此参数,此项不参与sign签名过程
    #tradeid:用户自定义订单号为数字(最多15位，唯一值),此项不参与sign签名过程
    def sellMarket(self, coinType, amount, tradePassword, tradeid):
        HuobiService.sellMarket(coinType, amount, tradePassword, tradeid, HuobiUtil.SELL_MARKET)
        pass
    #"查询个人最新10条成交订单"
    #coinType:币种 1 比特币 2 莱特币
    def getNewDealOrders(self, coinType):
        HuobiService.getNewDealOrders(coinType, HuobiUtil.NEW_DEAL_ORDERS)
        pass
    #"根据trade_id查询order_id"
    #coinType:币种 1 比特币 2 莱特币
    #tradeid:调用下单接口时的参数trade_id
    def getOrderIdByTradeId(self, coinType, tradeid):
        HuobiService.getOrderIdByTradeId(coinType, tradeid, HuobiUtil.ORDER_ID_BY_TRADE_ID)
        pass    
    #"取消订单接口"
    #coinType:币种 1 比特币 2 莱特币
    #orderId:要取消的委托id
    def cancelOrder(self, coinType, orderId):
        HuobiService.cancelOrder(coinType, orderId, HuobiUtil.CANCEL_ORDER)
        pass

