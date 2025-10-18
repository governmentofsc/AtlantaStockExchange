# simulator.py
import math
import random
import csv
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

def gbm_step(S, mu, sigma, dt=1/252):
    """Geometric Brownian Motion one-step."""
    # dS = mu*S*dt + sigma*S*sqrt(dt)*Z
    Z = random.gauss(0, 1)
    return S * math.exp((mu - 0.5 * sigma**2) * dt + sigma * math.sqrt(dt) * Z)

class MarketSimulator:
    def __init__(self, tickers, start_price=100.0, mu=0.0, sigma=0.02):
        # tickers: list of strings
        self.tickers = tickers
        self.mu = mu
        self.sigma = sigma
        # store history as dict[ticker] -> list of (timestamp, price)
        self.history = {t: [] for t in tickers}
        # initialize
        now = datetime.utcnow()
        for t in tickers:
            price = start_price * (1 + random.uniform(-0.1, 0.1))
            self.history[t].append((now, price))

    def step(self, dt=1/252):
        now = self.history[self.tickers[0]][-1][0] + timedelta(days=1)  # simple daily ticks
        for t in self.tickers:
            last_price = self.history[t][-1][1]
            new_price = gbm_step(last_price, self.mu, self.sigma, dt)
            # enforce a min price
            new_price = max(0.01, new_price)
            self.history[t].append((now, new_price))
        return now

    def to_dataframe(self):
        rows = []
        for t in self.tickers:
            for ts, price in self.history[t]:
                rows.append({"ticker": t, "timestamp": ts, "price": price})
        df = pd.DataFrame(rows)
        df.sort_values(["ticker", "timestamp"], inplace=True)
        return df

    def save_csv(self, filename="prices.csv"):
        df = self.to_dataframe()
        df.to_csv(filename, index=False)

if __name__ == "__main__":
    # quick demo
    sim = MarketSimulator(["AAA", "BBB", "CCC"], start_price=50, mu=0.0002, sigma=0.02)
    for _ in range(200):  # simulate 200 daily ticks
        sim.step()
    sim.save_csv("prices_demo.csv")
    print("Saved prices_demo.csv")
