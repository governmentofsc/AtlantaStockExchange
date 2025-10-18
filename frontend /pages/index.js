import useSWR from "swr";
import { useEffect, useState } from "react";
import axios from "axios";
import PriceChart from "../components/PriceChart";

const fetcher = url => axios.get(url).then(r => r.data);

export default function Home() {
  const { data: stocks } = useSWR("/api/stocks", fetcher, { refreshInterval: 5000 });
  const [wsData, setWsData] = useState({});

  useEffect(() => {
    const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws");
    ws.onmessage = evt => {
      const msg = JSON.parse(evt.data);
      if (msg.type === "price_update") {
        setWsData(prev => ({ ...prev, [msg.ticker]: msg.price }));
      }
    };
    return () => ws.close();
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold">Atlanta Stock Exchange</h1>
      <div className="grid grid-cols-3 gap-4 mt-6">
        {stocks?.map(s => {
          const live = wsData[s.ticker] ?? s.current_price;
          return (
            <div key={s.ticker} className="p-4 border rounded">
              <div className="flex justify-between">
                <div><strong>{s.ticker}</strong><div className="text-sm">{s.name}</div></div>
                <div className="text-lg">${live.toFixed(2)}</div>
              </div>
              <div className="mt-3">
                <PriceChart ticker={s.ticker} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
