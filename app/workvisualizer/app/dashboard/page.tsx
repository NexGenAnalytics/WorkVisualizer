import GlobalIndentedTree from '@/app/ui/components/GlobalIndentedTree';
import SpaceTime from '@/app/ui/components/SpaceTime';
import { redirect } from 'next/navigation';

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
    const res = await fetch('http://127.0.0.1:8000/api/global_hierarchy')
    try {
        const res = await fetch('http://127.0.0.1:8000/api/spacetime')

        if (!res.ok) {
            throw new Error('Failed to fetch data')
        }
        const jsonData = await res.json();
        console.log(jsonData)

        if (jsonData.message === "No file was uploaded.") {
            console.log(jsonData.message);
            // setError('No file was uploaded.');
            redirect('/'); // Redirecting to the landing page
        }

        return jsonData
    } catch (error) {
        console.error(error)
    }
}
