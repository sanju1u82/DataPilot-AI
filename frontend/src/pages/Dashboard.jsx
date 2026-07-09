import { useLocation } from "react-router-dom";
import Navbar from "../components/Layout/Navbar";

function Dashboard() {

    const location = useLocation();

    const profile = location.state?.profile;

    return (
        <>
            <Navbar />

            <div className="container mt-5">

                <h1>Dataset Dashboard</h1>

                <pre>
                    {JSON.stringify(profile, null, 2)}
                </pre>

            </div>
        </>
    );
}

export default Dashboard;