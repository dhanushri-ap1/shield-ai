function Sidebar({
    activePage,
    setActivePage
}) {

    const menuItems = [

        {
            id: "overview",
            icon: "◈",
            label: "Overview"
        },

        {
            id: "transactions",
            icon: "▣",
            label: "Transactions"
        },

        {
            id: "analytics",
            icon: "◌",
            label: "Analytics"
        }

    ];


    return (

        <aside className="sidebar">

            <div className="sidebar-brand">

                <div className="shield-logo">
                    S
                </div>


                <div>

                    <h1>
                        SHIELD-AI
                    </h1>

                    <span>
                        Risk Intelligence
                    </span>

                </div>

            </div>


            <div className="nav-section">

                <p>
                    WORKSPACE
                </p>


                {menuItems.map(
                    (item) => (

                        <button
                            key={item.id}
                            className={
                                `nav-item ${
                                    activePage === item.id
                                        ? "active"
                                        : ""
                                }`
                            }
                            onClick={() =>
                                setActivePage(
                                    item.id
                                )
                            }
                        >

                            <span className="nav-icon">
                                {item.icon}
                            </span>


                            {item.label}

                        </button>

                    )
                )}

            </div>


            <div className="sidebar-footer">

                <div className="system-indicator">

                    <span></span>

                    System Operational

                </div>


                <p>
                    SHIELD-AI v2.0
                </p>

            </div>

        </aside>

    );

}


export default Sidebar;