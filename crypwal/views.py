from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from .models import WalletItem

def index(request):
    if request.user.is_authenticated == False:
        return render(request, 'home.html')
    elif request.user.is_authenticated == True:
        all_wallet_items = WalletItem.objects.filter(user=request.user)
        return render(request, 'wallet.html',
        {'all_items':all_wallet_items}) 
    
def addWalletView(request):
    x = request.POST['content']
    amt = request.POST['amount']
    if x != '' and amt != '' and isinstance(amt, str) == False:
        new_item = WalletItem(user = request.user, content = x, amount = float(amt))
        new_item.save()
        return HttpResponseRedirect('/')
    else:
        return HttpResponseRedirect('/')

def deleteWalletView(request, i):
    y = WalletItem.objects.get(id= i)
    y.delete()
    return HttpResponseRedirect('/') 