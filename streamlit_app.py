import streamlit as st
import requests
import pandas as pd
from snowflake.snowpark.functions import col

# Title
st.title("Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruit you want with your smoothie.")

# Name input
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name of your Smoothie will be:', name_on_order)

# Snowflake connection
cnx = st.connection("snowflake")
session = cnx.session()

# Get fruit options
my_dataframe = session.table("SMOOTHIES.public.FRUIT_OPTIONS").select(col('FRUIT_NAME'), col('SEARCH_ON'))
pd_df = my_dataframe.to_pandas()

# Multiselect from Pandas column
fruit_options = pd_df['FRUIT_NAME'].tolist()
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    fruit_options,
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''
    
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        
        # Look up the 'SEARCH_ON' value safely
        search_match = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON']
        if not search_match.empty:
            search_on = search_match.iloc[0]
            st.subheader(f"{fruit_chosen} Nutrition Information")
            
            # Make sure URL is formed correctly
            try:
                api_url = f"https://my.smoothiefroot.com/api/fruit/{search_on}"
                smoothiefroot_response = requests.get(api_url)
                if smoothiefroot_response.status_code == 200:
                    st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)
                else:
                    st.warning(f"Could not fetch nutrition info for {fruit_chosen}.")
            except Exception as e:
                st.error(f"Error fetching data: {e}")
        else:
            st.warning(f"No 'SEARCH_ON' value found for {fruit_chosen}.")

    # Prepare insert statement
    my_insert_stmt = f"""
        INSERT INTO SMOOTHIES.public.ORDERS(ingredients, name_on_order)
        VALUES ('{ingredients_string.strip()}', '{name_on_order}')
    """
    st.write(my_insert_stmt)

    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success('Your Smoothie is ordered!', icon="✅")

# Optional: Show default fruit data
default_response = requests.get("https://my.smoothiefroot.com/api/fruit/watermelon")
if default_response.status_code == 200:
    st.dataframe(data=default_response.json(), use_container_width=True)
