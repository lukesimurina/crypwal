from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from .models import WalletItem
from django.contrib import messages
######################################################################################
############### CRYPTO PRICE GETTER ##################################################
######################################################################################

import requests
import time
import datetime
import typing
import os
from typing import Union, Optional, List, Dict
Timestamp = Union[datetime.datetime, datetime.date, int, float]

# API
_API_KEY_PARAMETER = ""
_URL_COIN_LIST = 'https://www.cryptocompare.com/api/data/coinlist?'
_URL_PRICE = 'https://min-api.cryptocompare.com/data/pricemulti?fsyms={}&tsyms={}'
_URL_PRICE_MULTI = 'https://min-api.cryptocompare.com/data/pricemulti?fsyms={}&tsyms={}'
_URL_PRICE_MULTI_FULL = 'https://min-api.cryptocompare.com/data/pricemultifull?fsyms={}&tsyms={}'
_URL_HIST_PRICE = 'https://min-api.cryptocompare.com/data/pricehistorical?fsym={}&tsyms={}&ts={}&e={}'
_URL_HIST_PRICE_DAY = 'https://min-api.cryptocompare.com/data/histoday?fsym={}&tsym={}&limit={}&e={}&toTs={}'
_URL_HIST_PRICE_HOUR = 'https://min-api.cryptocompare.com/data/histohour?fsym={}&tsym={}&limit={}&e={}&toTs={}'
_URL_HIST_PRICE_MINUTE = 'https://min-api.cryptocompare.com/data/histominute?fsym={}&tsym={}&limit={}&e={}&toTs={}'

# DEFAULTS
CURRENCY = 'EUR'
LIMIT = 1440


def _query_cryptocompare(url: str, errorCheck: bool = True, api_key: str = None) -> Optional[Dict]:
    api_key_parameter = _set_api_key_parameter(api_key)
    try:
        response = requests.get(url + api_key_parameter).json()
    except Exception as e:
        print('Error getting coin information. %s' % str(e))
        return None
    if errorCheck and (response.get('Response') == 'Error'):
        print('[ERROR] %s' % response.get('Message'))
        return None
    return response

def _format_parameter(parameter: object) -> str:
    if isinstance(parameter, list):
        return ','.join(parameter)

    else:
        return str(parameter)
    
def _format_timestamp(timestamp: Timestamp) -> int:
    """
    Format the timestamp depending on its type and return
    the integer representation accepted by the API.
    :param timestamp: timestamp to format
    """
    if isinstance(timestamp, datetime.datetime) or isinstance(timestamp, datetime.date):
        return int(time.mktime(timestamp.timetuple()))
    return int(timestamp)

def get_price(coin: str, currency: str = CURRENCY, full: bool = False) -> Optional[Dict]:
    if full:
        return _query_cryptocompare(
            _URL_PRICE_MULTI_FULL.format(
                _format_parameter(coin), _format_parameter(currency))
        )
    if isinstance(coin, list):
        return _query_cryptocompare(
            _URL_PRICE_MULTI.format(_format_parameter(coin),
                                    _format_parameter(currency))
        )
    return _query_cryptocompare(
        _URL_PRICE.format(coin, _format_parameter(currency))
    )

def _set_api_key_parameter(api_key: str = None) -> str:
    if api_key is None:
        api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    if api_key is not None:
        _API_KEY = "&api_key={}".format(api_key)
        return _API_KEY
    return ""

def get_historical_price(coin: str, currency: str = CURRENCY, timestamp: Timestamp = time.time(),
                         exchange: str = 'CCCAGG') -> Optional[Dict]:
    """
    Get the price of a coin in a given currency during a specific time.
    :param coin: symbolic name of the coin (e.g. BTC)
    :param currency: short hand description of the currency (e.g. EUR)
    :param timestamp: point in time
    :param exchange: the exchange to use
    :returns: dict of coin and currency price pairs
    """
    return _query_cryptocompare(
        _URL_HIST_PRICE.format(coin,
                               _format_parameter(currency),
                               _format_timestamp(timestamp),
                               _format_parameter(exchange))
    )


###############################################################################


def getCryptoPrice(wallet_list, currency):
    price = get_price(wallet_list, currency)
    return price

def getCryptoPriceDay(coin, currency):
    price = get_historical_price(coin, currency, (datetime.datetime.now() - datetime.timedelta(days=1)))
    return price

def index(request):
    if request.user.is_authenticated == False:
        return render(request, 'home.html')
    elif request.user.is_authenticated == True:
        all_wallet_items = WalletItem.objects.filter(user=request.user)
        all_wallet_item_names = []
        for i in all_wallet_items:
            all_wallet_item_names.append(i.content)
        prices = {}
        dayPrices = {}
        if all_wallet_item_names != []:
            prices = getCryptoPrice(all_wallet_item_names, 'USD')
            dayPrices = {}
            for i in all_wallet_item_names:
                dayPrices[i] = getCryptoPriceDay(i, 'USD')[all_wallet_items.get(content=i).content]['USD']
            
            for i in all_wallet_items:
                i.price = prices[i.content]['USD']
                i.value = round(prices[i.content]['USD'] * i.amount, 2)
                i.dayValue = round(dayPrices[i.content] * i.amount, 2)
                previous = i.dayValue
                current = i.value
                i.dayValueChange = round((current - previous) / previous * 100, 2)
                i.save()
        
        total = 0
        if prices is not None:
            for i in prices:
                total += prices[i]['USD'] * all_wallet_items.get(content=i).amount
        total = round(total, 2)
        
        day_total = 0
        if dayPrices is not None:
            for i in dayPrices:
                day_total += dayPrices[i] * all_wallet_items.get(content=i).amount
        day_total = round(day_total, 2)
        try:
            day_change = round((total - day_total) / day_total * 100, 2)
        except ZeroDivisionError:
            day_change = 0
        
        return render(request, 'wallet.html',{'all_items':all_wallet_items,'prices':prices, 'total':total, 'day_total':day_total, 'day_change':day_change})
    
def addWalletView(request):
    x = request.POST['content']
    amt = request.POST['amount']
    if get_price(x, 'USD') is not None:
        if x != '' and WalletItem.objects.filter(user=request.user, content=x).exists():
            try:
                amt = float(amt)
            except:
                messages.warning(request, 'Amount must be a number')
                return HttpResponseRedirect('/')
            if amt != '':
                existing_amt = WalletItem.objects.get(user=request.user, content=x).amount
                WalletItem.objects.filter(user=request.user, content=x).update(amount=existing_amt + amt)
                messages.success(request, 'Added ' + str(amt) + ' ' + x + ' to your wallet')
            else:
                messages.info(request, 'Please enter a valid item and amount')
                return HttpResponseRedirect('/')
        else:
            try:
                amt = float(amt)
            except:
                messages.info(request, 'Amount must be a number')
                return HttpResponseRedirect('/')
            if x != '' and amt != '':
                new_item = WalletItem(user = request.user, content = x, amount = float(amt))
                new_item.save()
                messages.success(request, 'Added ' + str(amt) + ' ' + x + ' to your wallet')
                return HttpResponseRedirect('/')
            else:
                messages.info(request, 'Please enter a valid item and amount')
                return HttpResponseRedirect('/')
    return HttpResponseRedirect('/')

def deleteWalletView(request, i):
    y = WalletItem.objects.get(id= i)
    y.delete()
    messages.success(request, y.content + ' deleted from wallet')
    return HttpResponseRedirect('/') 