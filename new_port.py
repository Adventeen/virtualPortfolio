from datetime import datetime
import yfinance as yf
from tabulate import tabulate
import os
import sys
from io import StringIO
import csv
import numpy as np
from matplotlib import pyplot as plt

class NullIO(StringIO):
    def write(self, txt):
        pass

def silent(fn):
    """Decorator to silence functions."""
    def silent_fn(*args, **kwargs):
        saved_stdout = sys.stdout
        sys.stdout = NullIO()
        result = fn(*args, **kwargs)
        sys.stdout = saved_stdout
        return result
    return silent_fn

get_data = silent(yf.download)

def import_csv(name):
    data = {
        'date_purchased': [],
        'symbol': [],
        'avg_price': [],
        'qty': [],
    }
    csv_file = open(f'{name}.csv', 'r')
    csv_reader = csv.reader(csv_file)
    count = 0
    for row in csv_reader:
        if count == 0:
            initial = float(row[1])
            cash = float(row[2])
            brokerage = float(row[3])
            count+=1
        else:
            data['date_purchased'].append(row[0])
            data['symbol'].append(row[1])
            data['avg_price'].append(float(row[2]))
            data['qty'].append(float(row[3]))

    csv_file.close()
    return Portfolio(name, initial, cash, brokerage, data)

class Portfolio(object):
    """docstring for Portfolio."""
    def __init__(self, name, initial, cash, brokerage, data):
        self.name = name
        self.initial = initial
        self.cash = cash
        self.brokerage = brokerage
        self.data = data
        self.current = []

        self.get_current()

    def get_current(self):
        for i in self.data['symbol']:
            price = round(get_data(f'{i}.NS', period='1d').iloc[0]['Adj Close'], 2)
            self.current.append(price)

    def display_port(self):
        os.system('cls')
        data = self.data.copy()
        initial_value = [p * q for p, q in zip(self.data['avg_price'], self.data['qty'])]
        current_value = [p * q for p, q in zip(self.current, self.data['qty'])]
        ret = [round((c/i - 1) * 100, 2) for i, c in zip(self.data['avg_price'], self.current)]
        data['initial_value'] = initial_value
        data['current_price'] = self.current
        data['current_value'] = current_value
        data['ret'] = ret
        port_val = sum(current_value)
        print(self.name)
        print(f'Initial Investment: {round(self.initial, 2)}')
        print(f'Cash: {round(self.cash, 2)}')
        print(f'Portfolio Value: {round(port_val, 2)}')
        print(f'Total Value: {round(self.cash + port_val, 2)}')
        print(f'Portfolio Return: {round(((self.cash + port_val)/self.initial - 1) * 100, 2)}')
        print(f'Brokerage Paid: {round(self.brokerage, 2)}')
        print()
        print(tabulate(data, headers=['PurchasedOn', 'Stock', 'AvgPrice', 'QTY', 'Value', 'LTP', 'CurrentValue', 'Return']))

    def buy(self, stock, qty):
        try:
            price = round(get_data(f'{stock}.NS', period='1d').iloc[0]['Adj Close'], 2)
            brokerage = round(price * qty * 0.00118835, 2)
            cost = round(price * qty, 2) + brokerage
            if(self.cash - cost >= 0):
                if(stock not in self.data['symbol']):
                    self.data['date_purchased'].append(datetime.now().date())
                    self.data['symbol'].append(stock)
                    self.data['avg_price'].append(price)
                    self.data['qty'].append(qty)
                    self.current.append(price)
                else:
                    i = self.data['symbol'].index(stock)
                    avg = round(((self.data['qty'][i] * self.data['avg_price'][i]) + (price * qty))/(self.data['qty'][i] + qty), 2)
                    self.data['qty'][i] += qty
                    self.data['avg_price'][i] = avg
                    self.current[i] = price

                self.cash -= cost
                self.brokerage += brokerage
            else:
                err = input('Not enough money')
        except Exception as e:
            err = input('No such stock')

    def sell(self, stock, qty):
        if(stock in self.data['symbol']):
            i = self.data['symbol'].index(stock)
            if(self.data['qty'][i] > qty):
                sell_price = self.current[i]
                brokerage = round(sell_price * qty * 0.00103835, 2)
                self.cash += (sell_price * qty)
                self.cash -= brokerage
                self.brokerage += brokerage
                self.data['qty'][i] -= qty

            elif(self.data['qty'][i] == qty):
                sell_price = self.current[i]
                brokerage = round(sell_price * qty * 0.00103835, 2)
                self.cash += (sell_price * qty)
                self.cash -= brokerage
                self.brokerage += brokerage

                for value in self.data.values():
                    del value[i]

                del self.current[i]
            else:
                err = input('Not enough qty of stock')
        else:
            err = input('Stock not in portfolio')

    def show_graph(self):
        price1 = get_data(f'{self.data["symbol"][0]}.NS', period='3mo')['Adj Close'].to_list()
        total = np.array([price * self.data['qty'][0] for price in price1], dtype=np.float64)
        for stock in self.data['symbol']:
            hist_price = get_data(f'{stock}.NS', period='3mo')['Adj Close'].to_list()
            wt_price = np.array([price * self.data['qty'][self.data['symbol'].index(stock)] for price in hist_price], dtype=np.float64)
            total = np.add(total, wt_price)

        time = [i for i in range(len(total))]

        plt.style.use('ggplot')
        plt.plot(time, total)
        plt.grid(True)
        plt.show()


    def export_csv(self):
        csv_file = open(f'{self.name}.csv', 'w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([str(datetime.now().date()), self.initial, self.cash, self.brokerage])

        for i in range(len(self.current)):
            lst = []
            for key in self.data.keys():
                lst.append(self.data[key][i])
            csv_writer.writerow(lst)

        csv_file.close()

while True:
    txt = input("""
New Portfolio: NEW
Open Portfolio: OPEN
Quit: QUIT
""")
    if(txt == 'NEW'):
        data = {
            'date_purchased': [],
            'symbol': [],
            'avg_price': [],
            'qty': [],
        }
        name = input("Enter name of portfolio: ")
        initial = float(input("Enter initial amount: "))
        p1 = Portfolio(name, initial, initial, 0, data)
        p1.export_csv()
    elif(txt == 'OPEN'):
        pname = input("Enter name of portfolio: ")
        try:
            p1 = import_csv(pname)
            while True:
                p1.display_port()
                ch = input("Enter the action: ")
                if(ch == "BUY"):
                    name = input("Enter symbol of stock: ")
                    qty = float(input("Enter qty: "))
                    p1.buy(name, qty)
                elif(ch == 'SELL'):
                    name = input("Enter stock from portfolio: ")
                    qty = float(input("Enter qty: "))
                    p1.sell(name, qty)
                elif(ch == 'GRAPH'):
                    p1.show_graph()
                else:
                    p1.export_csv()
                    break
        except Exception as e:
            print(f'No portfolio named {pname}')
            # print(e)
    else:
        break

# p1 = import_csv('Trial1')
# print(p1.show_graph())
