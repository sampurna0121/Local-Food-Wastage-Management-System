import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
import plotly.express as px


# DB connection
engine = create_engine("postgresql://postgres:PASSsql@localhost:5432/food_waste_db")

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home", "📄 Query Results", "📈 Visualizations", "🛠️ Manage Listings"])

# ----------------------- 🏠 Home -----------------------
if page == "🏠 Home":
    st.title("🍲 Local Food Wastage Management System")

    st.write("## Welcome to the Food Wastage Management System")
    st.markdown("""c
    - **🥦 Food Providers** list surplus food  
    - **🛒 Receivers** can claim food in need  
    - 🔍 Analyze food wastage trends using SQL  
    - 📊 Visualize key insights from the data  
    """)

# ----------------------- 📄 Query Results -----------------------
elif page == "📄 Query Results":
    st.title("📄 SQL Query Results")

# Query 1: food providers and receivers are there in each city
    q1 = """
    SELECT city,
        COUNT(DISTINCT provider_id) AS provider_count,
        COUNT(DISTINCT receiver_id) AS receiver_count
    FROM (
        SELECT city, provider_id, NULL::int AS receiver_id FROM providers
        UNION ALL
        SELECT city, NULL::int AS provider_id, receiver_id FROM receivers
    ) AS all_participants
    GROUP BY city
    ORDER BY city;
    """
    df1 = pd.read_sql(q1, engine)
    st.subheader("1. Food Providers and Receivers per City")
    st.dataframe(df1)

# Query 2: Total food contribution by provider type
    q2 = """
    SELECT provider_type,
           SUM(quantity) AS total_quantity
    FROM food_listings
    GROUP BY provider_type
    ORDER BY total_quantity DESC;
    """

    df2 = pd.read_sql(q2, engine)
    st.subheader("2. Food Contribution by Provider Type")
    st.dataframe(df2)

# Query 3: Contact Info of Food Providers in a Specific City
    # Step 1: Get all distinct cities from the providers table
    city_query = "SELECT DISTINCT city FROM providers ORDER BY city;"
    cities = pd.read_sql(city_query, engine)['city'].tolist()
    st.subheader("3. Contact Info of Food Providers in a Specific City")
    
    # Step 2: Let user select a city from a dropdown
    selected_city = st.selectbox("Select a City", options=cities)

    # Step 3: Query providers by selected city
    if selected_city:
        q3 = """
        SELECT name, contact, type, city
        FROM providers
        WHERE city = %s;
        """
        df3 = pd.read_sql(q3, engine, params=(selected_city,))

        if not df3.empty:
            st.write("### Provider Details:")
            st.dataframe(df3)
        else:
            st.warning("No providers found in the selected city.")

# Query 4:Top Receivers by Total Food Claimed
    q4 = """
    SELECT r.name AS receiver_name,
           r.city,
           SUM(f.quantity) AS total_claimed_quantity
    FROM claims c
    JOIN receivers r ON c.receiver_id = r.receiver_id
    JOIN food_listings f ON c.food_id = f.food_id
    WHERE c.status = 'Completed'
    GROUP BY r.receiver_id, r.name, r.city
    ORDER BY total_claimed_quantity DESC;
    """

    df4 = pd.read_sql(q4, engine)

    if not df4.empty:
        st.subheader("4. Receivers Who Claimed the Most Food")
        st.dataframe(df4)

#Query 5:Total Quantity of Food Available from All Providers
    q5 = """
    SELECT SUM(quantity) AS total_available_quantity
    FROM food_listings;
    """

    df5 = pd.read_sql(q5, engine)

    st.subheader("5. Total Quantity of Food Available from All Providers")
    st.dataframe(df5)
    st.write("Query Result:", df5)

    # Query 6: Location with the Highest Number of Food Listings
    q6 = """
    SELECT location, COUNT(*) AS listing_count
    FROM food_listings
    GROUP BY location
    ORDER BY listing_count DESC
    LIMIT 1;
    """
    df6 = pd.read_sql(q6, engine)
    st.subheader("6. Location with the Highest Number of Food Listings")
    st.dataframe(df6)

    # Query 7: Most Commonly Available Food Types
    q7 = """
        SELECT food_type, COUNT(*) AS total_count
        FROM food_listings
        GROUP BY food_type
        ORDER BY total_count DESC;
    """
    df7 = pd.read_sql(q7, engine)

    st.subheader("7. Most Commonly Available Food Types")
    st.dataframe(df7)

    # Query 8: Number of Claims per Food Item
    st.subheader("8. Number of Claims per Food Item")

    q8 = """
        SELECT f.food_name, COUNT(c.claim_id) AS total_claims
        FROM claims c
        JOIN food_listings f ON c.food_id = f.food_id
        GROUP BY f.food_name
        ORDER BY total_claims DESC;
    """
    try:
        df8 = pd.read_sql(q8, engine)
        st.dataframe(df8)
    except Exception as e:
        st.error(f"❌ Error fetching data for Query 8: {e}")

    # Query 9: Provider with Highest Number of Successful Food Claims
    st.subheader("9. Provider with Highest Number of Successful Food Claims")

    q9 = """
        SELECT p.name AS provider_name,
               COUNT(c.claim_id) AS successful_claims
        FROM claims c
        JOIN food_listings f ON c.food_id = f.food_id
        JOIN providers p ON f.provider_id = p.provider_id
        WHERE c.status = 'Completed'
        GROUP BY p.name
        ORDER BY successful_claims DESC
        LIMIT 1;
    """
    try:
        df9 = pd.read_sql(q9, engine)
        st.dataframe(df9)
    except Exception as e:
        st.error(f"❌ Error fetching data for Query 9: {e}")

    # Query 10: Percentage of Food Claims by Status
    st.subheader("10. Percentage of Food Claims by Status")

    q10 = """
        SELECT status,
               COUNT(*) AS total,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentage
        FROM claims
        GROUP BY status
        ORDER BY total DESC;
    """

    try:
        df10 = pd.read_sql(q10, engine)
        st.dataframe(df10)
    except Exception as e:
        st.error(f"❌ Error fetching data for Query 10: {e}")

    # Query 11: Average Quantity of Food Claimed per Receiver
    st.subheader("11. Average Quantity of Food Claimed per Receiver")

    q11 = """
        SELECT 
            r.name AS receiver_name,
            r.city,
            ROUND(AVG(f.quantity), 2) AS avg_claimed_quantity
        FROM claims c
        JOIN receivers r ON c.receiver_id = r.receiver_id
        JOIN food_listings f ON c.food_id = f.food_id
        WHERE c.status = 'Completed'
        GROUP BY r.receiver_id, r.name, r.city
        ORDER BY avg_claimed_quantity DESC;
    """

    try:
        df11 = pd.read_sql(q11, engine)
        if not df11.empty:
            st.dataframe(df11)
        else:
            st.warning("⚠️ No data found for completed claims.")
    except Exception as e:
        st.error(f"❌ Error fetching data for Query 11: {e}")

    # Query 12: Most Claimed Meal Type
    st.subheader("12. Most Claimed Meal Type")

    q12 = """
        SELECT f.meal_type, 
               COUNT(c.claim_id) AS total_claims
        FROM claims c
        JOIN food_listings f ON c.food_id = f.food_id
        WHERE c.status = 'Completed'
        GROUP BY f.meal_type
        ORDER BY total_claims DESC;
    """

    try:
        df12 = pd.read_sql(q12, engine)

        if not df12.empty:
            st.dataframe(df12)
        else:
            st.warning("⚠️ No data found for claimed meal types.")

    except Exception as e:
        st.error(f"❌ Error fetching data for Query 12: {e}")

if page == "📄 Query Results":
    # Query 13: Total Quantity of Food Donated by Each Provider
    st.subheader("13. Total Quantity of Food Donated by Each Provider")

    q13 = """
        SELECT p.name AS provider_name,
               p.city,
               SUM(f.quantity) AS total_donated_quantity
        FROM food_listings f
        JOIN providers p ON f.provider_id = p.provider_id
        GROUP BY p.name, p.city
        ORDER BY total_donated_quantity DESC;
    """

    try:
        df13 = pd.read_sql(q13, engine)
        if not df13.empty:
            st.dataframe(df13)
        else:
            st.warning("⚠️ No data found for food donations.")
    except Exception as e:
        st.error(f"❌ Error fetching data for Query 13: {e}")


# ----------------------- 📈 Visualizations -----------------------

elif page == "📈 Visualizations":
    st.title("📈 Visualizations")
    
    # Query 1
    q1 = """
    SELECT city,
           COUNT(DISTINCT provider_id) AS providers,
           COUNT(DISTINCT receiver_id) AS receivers
    FROM (
        SELECT city, provider_id, NULL::int AS receiver_id FROM providers
        UNION ALL
        SELECT city, NULL::int, receiver_id FROM receivers
    ) AS combined
    GROUP BY city ORDER BY city;
    """
    df1 = pd.read_sql(q1, engine)
    df1["total"] = df1["providers"] + df1["receivers"]
    df1 = df1.sort_values(by="total", ascending=False).head(20)
    st.subheader("1. Top 20 Cities: Food Providers and Receivers")
    if not df1.empty:
        df1_melted = df1.melt(id_vars="city", value_vars=["providers", "receivers"], var_name="type", value_name="count")
        fig, ax = plt.subplots(figsize=(10, 7))
        sns.barplot(data=df1_melted, y="city", x="count", hue="type", ax=ax, palette="Set2", orient="h")
        ax.set(title="Top 20 Cities: Providers and Receivers", xlabel="Count", ylabel="City")
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.warning("No data available for this query.")

    # Query 2
    q2 = """
    SELECT f.provider_type,
           SUM(f.quantity) AS total_quantity
    FROM food_listings f
    GROUP BY f.provider_type
    ORDER BY total_quantity DESC;
    """
    df2 = pd.read_sql(q2, engine)
    st.subheader("2. Food Contribution by Provider Type")
    if not df2.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=df2, x="total_quantity", y="provider_type", palette="viridis", ax=ax)
        ax.set_title("Total Food Quantity Donated by Provider Type")
        ax.set_xlabel("Total Quantity Donated")
        ax.set_ylabel("Provider Type")
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.warning("No data available for this query.")

    # Query 3
    st.subheader("3. Contact Info of Food Providers in a Specific City")
    city_query = "SELECT DISTINCT city FROM providers ORDER BY city;"
    cities = pd.read_sql(city_query, engine)['city'].tolist()
    selected_city = st.selectbox("Select a City", options=cities)
    if selected_city:
        q3 = """
        SELECT name, contact, type, city
        FROM providers
        WHERE city = %s;
        """
        df3 = pd.read_sql(q3, engine, params=(selected_city,))
        if not df3.empty:
            fig = px.pie(df3, names='type', title=f"Provider Distribution in {selected_city}")
            st.plotly_chart(fig)

    # Query 4
    q4 = """
    SELECT r.name AS receiver_name,
           r.city,
           SUM(f.quantity) AS total_claimed_quantity
    FROM claims c
    JOIN receivers r ON c.receiver_id = r.receiver_id
    JOIN food_listings f ON c.food_id = f.food_id
    WHERE c.status = 'Completed'
    GROUP BY r.receiver_id, r.name, r.city
    ORDER BY total_claimed_quantity DESC;
    """
    df4 = pd.read_sql(q4, engine)
    st.subheader("4. Receivers Who Claimed the Most Food")
    if not df4.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(data=df4.head(10), x="receiver_name", y="total_claimed_quantity", ax=ax, palette="mako")
        ax.set_title("Top Receivers by Quantity of Food Claimed")
        ax.set_xlabel("Receiver Name")
        ax.set_ylabel("Total Quantity Claimed")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.warning("No data available for this query.")

    # Query 5
    st.subheader("5. Total Quantity of Food Available from All Providers")
    q5 = """
    SELECT SUM(quantity) AS total_available_quantity
    FROM food_listings;
    """
    try:
        df5 = pd.read_sql(q5, engine)
        if not df5.empty and df5.iloc[0]["total_available_quantity"] is not None:
            total_qty = int(df5.iloc[0]["total_available_quantity"])
            st.metric(label="Total Food Quantity", value=f"{total_qty:,} units")
            fig, ax = plt.subplots(figsize=(4, 3))
            ax.bar(["Total Available"], [total_qty], color="seagreen")
            ax.set_ylabel("Quantity")
            ax.set_title("Total Food Available")
            st.pyplot(fig)
        else:
            st.warning("No food data available to display.")
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")

    # Query 6
    st.subheader("6. Top 10 Locations by Number of Food Listings")
    q6 = """
    SELECT location, COUNT(*) AS listing_count
    FROM food_listings
    GROUP BY location
    ORDER BY listing_count DESC
    LIMIT 10;
    """
    df6 = pd.read_sql(q6, engine)
    if not df6.empty:
        fig, ax = plt.subplots()
        sns.barplot(data=df6, x="listing_count", y="location", palette="mako", ax=ax)
        ax.set_title("Top 10 Locations with Most Food Listings")
        ax.set_xlabel("Number of Listings")
        ax.set_ylabel("Location")
        st.pyplot(fig)
    else:
        st.warning("No data available for visualization.")

    # Query 7
    st.subheader("7. Most Commonly Available Food Types")
    q7 = """
    SELECT food_type, COUNT(*) AS total_count
    FROM food_listings
    GROUP BY food_type
    ORDER BY total_count DESC;
    """
    df7 = pd.read_sql(q7, engine)
    if not df7.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(data=df7, x="total_count", y="food_type", palette="crest", ax=ax)
        ax.set_title("Most Common Food Types Available")
        ax.set_xlabel("Number of Listings")
        ax.set_ylabel("Food Type")
        st.pyplot(fig)
    else:
        st.warning("No food type data available.")

    # Query 8: Number of Claims per Food Item
    st.subheader("8. Number of Claims per Food Item")

    q8 = """
        SELECT f.food_name,
               COUNT(c.claim_id) AS total_claims
        FROM claims c
        JOIN food_listings f ON c.food_id = f.food_id
        GROUP BY f.food_name
        ORDER BY total_claims DESC;
    """

    try:
        df8 = pd.read_sql(q8, engine)

        if not df8.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(data=df8.head(15), x="total_claims", y="food_name", palette="flare", ax=ax)
            ax.set_title("Top 15 Most Claimed Food Items")
            ax.set_xlabel("Number of Claims")
            ax.set_ylabel("Food Item")
            st.pyplot(fig)
        else:
            st.warning("No claims data available.")
    except Exception as e:
        st.error(f"❌ Error fetching data for Query 8: {e}")

    # Query 9: Top 10 Providers with Most Successful Food Claims
    st.subheader("9. Top 10 Providers with Most Successful Food Claims")

    q9 = """
        SELECT p.name AS provider_name,
               COUNT(c.claim_id) AS successful_claims
        FROM claims c
        JOIN food_listings f ON c.food_id = f.food_id
        JOIN providers p ON f.provider_id = p.provider_id
        WHERE c.status = 'Completed'
        GROUP BY p.name
        ORDER BY successful_claims DESC
        LIMIT 10;
    """
    try:
        df9 = pd.read_sql(q9, engine)

        if not df9.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.barplot(data=df9, x="successful_claims", y="provider_name", palette="rocket", ax=ax)
            ax.set_title("Top 10 Providers by Successful Food Claims")
            ax.set_xlabel("Number of Successful Claims")
            ax.set_ylabel("Provider Name")
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("No data available for Query 9.")
    except Exception as e:
        st.error(f"❌ Error fetching data for Query 9: {e}")

    # Query 10: Visualization – Claim Status Distribution (Pie Chart)
    st.subheader("10. Percentage of Food Claims by Status (Pie Chart)")

    q10_viz = """
        SELECT status,
               COUNT(*) AS total,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentage
        FROM claims
        GROUP BY status
        ORDER BY total DESC;
    """

    try:
        df10_viz = pd.read_sql(q10_viz, engine)

        if not df10_viz.empty:
            fig10 = px.pie(
                df10_viz,
                names='status',
                values='total',
                title='Distribution of Claim Status',
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig10)
        else:
            st.warning("No data found for Query 10 visualization.")
    except Exception as e:
        st.error(f"❌ Error generating visualization for Query 10: {e}")

    # Query 11: Average Quantity of Food Claimed per Receiver
    st.subheader("11. Average Quantity of Food Claimed per Receiver")

    q11 = """
        SELECT 
            r.name AS receiver_name,
            r.city,
            ROUND(AVG(f.quantity), 2) AS avg_claimed_quantity
        FROM claims c
        JOIN receivers r ON c.receiver_id = r.receiver_id
        JOIN food_listings f ON c.food_id = f.food_id
        WHERE c.status = 'Completed'
        GROUP BY r.receiver_id, r.name, r.city
        ORDER BY avg_claimed_quantity DESC;
    """

    try:
        df11 = pd.read_sql(q11, engine)

        if not df11.empty:
            # Visualization - Horizontal Bar Chart
            fig11 = px.bar(
                df11,
                x="avg_claimed_quantity",
                y="receiver_name",
                orientation="h",
                title="Average Quantity Claimed per Receiver",
                labels={
                    "avg_claimed_quantity": "Avg Quantity",
                    "receiver_name": "Receiver"
                }
            )
            fig11.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig11)
        else:
            st.warning("⚠️ No data found for completed claims.")

    except Exception as e:
        st.error(f"❌ Error fetching data for Query 11: {e}")

    # Query 12: Most Claimed Meal Type
    st.subheader("12. Most Claimed Meal Type")

    q12 = """
        SELECT f.meal_type, 
               COUNT(c.claim_id) AS total_claims
        FROM claims c
        JOIN food_listings f ON c.food_id = f.food_id
        WHERE c.status = 'Completed'
        GROUP BY f.meal_type
        ORDER BY total_claims DESC;
    """

    try:
        df12 = pd.read_sql(q12, engine)

        if not df12.empty:
            fig12 = px.pie(
                df12,
                names="meal_type",
                values="total_claims",
                title="Most Claimed Meal Type"
            )
            st.plotly_chart(fig12)
        else:
            st.warning("⚠️ No claims data available for meal types.")
    except Exception as e:
        st.error(f"❌ Error fetching data for Query 12: {e}")
        
# Query 13: Total Quantity of Food Donated by Each Provider
    st.subheader("13. Total Quantity of Food Donated by Each Provider")

    q13 = """
        SELECT p.name AS provider_name,
               SUM(f.quantity) AS total_donated_quantity
        FROM food_listings f
        JOIN providers p ON f.provider_id = p.provider_id
        GROUP BY p.name
        ORDER BY total_donated_quantity DESC
        LIMIT 10;
    """

    try:
        df13 = pd.read_sql(q13, engine)

        if not df13.empty:
            fig13 = px.bar(
                df13,
                x="total_donated_quantity",
                y="provider_name",
                orientation="h",
                title="Top 10 Providers by Total Food Donated",
                labels={
                    "total_donated_quantity": "Total Quantity Donated",
                    "provider_name": "Provider"
                }
            )
            fig13.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig13)
        else:
            st.warning("⚠️ No data found for food donations.")
    except Exception as e:
        st.error(f"❌ Error generating visualization for Query 13: {e}")

elif page == "🛠️ Manage Listings":
    st.title("🛠️ Manage Food Listings (CRUD)")

    # 📋 View existing food listings
    st.subheader("📋 Current Food Listings")
    try:
        food_df = pd.read_sql("SELECT * FROM food_listings ORDER BY food_id", engine)
        st.dataframe(food_df)
    except Exception as e:
        st.error(f"❌ Error fetching listings: {e}")

    st.markdown("---")

    # ➕ Add New Food Item
    st.subheader("➕ Add New Food Item")
    with st.form("add_form"):
        food_name = st.text_input("Food Name")
        quantity = st.number_input("Quantity", min_value=1)
        expiry_date = st.date_input("Expiry Date")
        provider_id = st.number_input("Provider ID", min_value=1)
        provider_type = st.selectbox("Provider Type", ["Restaurant", "Grocery Store", "Supermarket"])
        location = st.text_input("Location")
        food_type = st.selectbox("Food Type", ["Vegetarian", "Non-Vegetarian", "Vegan"])
        meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"])

        submitted = st.form_submit_button("Add Food")
        if submitted:
            insert_query = """
                INSERT INTO food_listings 
                (food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """
            try:
                with engine.begin() as conn:
                    conn.execute(insert_query, (food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type))
                st.success("✅ Food item added successfully!")
            except Exception as e:
                st.error(f"❌ Error: {e}")

    st.markdown("---")

    # ✏️ Update Food Item Quantity
    st.subheader("✏️ Update Food Quantity")
    update_id = st.number_input("Enter Food ID to Update", min_value=1)
    new_quantity = st.number_input("New Quantity", min_value=1, key="update_qty")
    if st.button("Update Quantity"):
        try:
            with engine.begin() as conn:
                conn.execute("UPDATE food_listings SET quantity = %s WHERE food_id = %s", (new_quantity, update_id))
            st.success("✅ Quantity updated!")
        except Exception as e:
            st.error(f"❌ Error: {e}")

    st.markdown("---")

    # 🗑️ Delete Food Item
    st.subheader("🗑️ Delete Food Item")
    delete_id = st.number_input("Enter Food ID to Delete", min_value=1, key="delete_id")
    if st.button("Delete Food"):
        try:
            with engine.begin() as conn:
                conn.execute("DELETE FROM food_listings WHERE food_id = %s", (delete_id,))
            st.success("🗑️ Food item deleted successfully!")
        except Exception as e:
            st.error(f"❌ Error: {e}")
