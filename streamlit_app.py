# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
from snowflake.snowpark import Session
import requests

# App title and instructions
st.title(":cup_with_straw: Customize your smoothie! :cup_with_straw:")
st.write("Choose the fruits you want to add to your custom Smoothie!")

# User input
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Connect to Snowflake
connection_parameters = st.secrets["connections"]["snowflake"]
session = Session.builder.configs(connection_parameters).create()

# Load fruit options
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
pd_df = my_dataframe.to_pandas()

# Fruit selection
fruit_names = pd_df['FRUIT_NAME'].tolist()
ingredients_list = st.multiselect('Choose up to 5 ingredients:', fruit_names, max_selections=5)

# Show nutrition info and prepare order
if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        # Get search term
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.write(f"The search value for {fruit_chosen} is {search_on}.")

        # Show nutrition info
        st.subheader(f"{fruit_chosen} Nutrition Information")
        api_url = f"https://my.smoothiefroot.com/api/fruit/{search_on.lower()}"
        response = requests.get(api_url)

        if response.status_code == 200:
            try:
                st.dataframe(response.json(), use_container_width=True)
            except Exception:
                st.error("Could not parse JSON from the API response.")
        else:
            st.error(f"API request failed with status code {response.status_code}")

    # Submit order
    if st.button('Submit Order'):
        insert_stmt = f"""
            INSERT INTO smoothies.public.orders (ingredients, name_on_order)
            VALUES ('{ingredients_string.strip()}', '{name_on_order}')
        """
        session.sql(insert_stmt).collect()
        st.success(f"Your Smoothie is ordered, {name_on_order}!", icon="✅")
