import BarChart from '../components/BarChart';

export default async function Page() {
    const data = await getData()
    return (
        <div>
            <h1>Sales Data</h1>
            <BarChart data={data} />
        </div>
    );
};

async function getData() {
    const res = await fetch('http://127.0.0.1:8000/api/sales')

    if (!res.ok) {
        throw new Error('Failed to fetch data')
    }

    return res.json()
}
