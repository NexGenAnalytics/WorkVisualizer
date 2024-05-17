import GlobalIndentedTree from '@/app/ui/components/GlobalIndentedTree';

export default async function Page() {
    const data = await getData()
    return (
        <div>
            <h1>Dashboard</h1>
            <GlobalIndentedTree data={data} />
        </div>
    );
};

async function getData() {
    const res = await fetch('http://127.0.0.1:8000/api/global_hierarchy')

    if (!res.ok) {
        throw new Error('Failed to fetch data')
    }

    return res.json()
}
