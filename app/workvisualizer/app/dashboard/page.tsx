import SpaceTime from '@/app/ui/components/SpaceTime';

export default async function Page() {
    const data = await getData()
    return (
        <div>
            <h1>Dashboard</h1>
            <SpaceTime data={data} />
        </div>
    );
};

async function getData() {
    const res = await fetch('http://127.0.0.1:8000/api/spacetime')

    if (!res.ok) {
        throw new Error('Failed to fetch data')
    }

    return res.json()
}
