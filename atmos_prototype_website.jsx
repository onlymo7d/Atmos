import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function AtmosPrototype() {
  const [prediction, setPrediction] = useState(null);

  const generatePrediction = () => {
    // Mock AI prediction
    const solar = Math.floor(Math.random() * 100);
    const wind = Math.floor(Math.random() * 100);

    let message = "";
    if (solar > 70) {
      message = "High solar output المتوقع! استخدم الأجهزة الآن.";
    } else if (wind > 70) {
      message = "High wind energy available! Run heavy machines.";
    } else {
      message = "Low renewable energy. Save power or use battery.";
    }

    setPrediction({ solar, wind, message });
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <h1 className="text-3xl font-bold mb-6 text-center">ATMOS Prototype</h1>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Prediction Card */}
        <Card className="rounded-2xl shadow-lg">
          <CardContent className="p-6">
            <h2 className="text-xl font-semibold mb-4">Energy Prediction</h2>
            <Button onClick={generatePrediction}>Generate Prediction</Button>

            {prediction && (
              <div className="mt-4">
                <p>☀️ Solar: {prediction.solar}%</p>
                <p>🌬 Wind: {prediction.wind}%</p>
                <p className="mt-2 font-medium">{prediction.message}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Smart Recommendations */}
        <Card className="rounded-2xl shadow-lg">
          <CardContent className="p-6">
            <h2 className="text-xl font-semibold mb-4">Smart Actions</h2>
            <ul className="list-disc ml-4 space-y-2">
              <li>Run washing machine during peak solar</li>
              <li>Charge EV when solar {'>'} 60%</li>
              <li>Shift heavy loads to high wind periods</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
