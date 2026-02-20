import json
import requests
import streamlit as st
from openai import OpenAI

# -------------------------
# Weather function (OpenWeatherMap)
# -------------------------
# location format examples:
#   "Syracuse, NY, US"
#   "Lima, Peru"
# units:
#   "imperial" => Fahrenheit
#   "metric"   => Celsius
def get_current_weather(location: str, units: str = "imperial") -> dict:
    api_key = st.secrets["OPENWEATHER_API_KEY"]

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": location, "appid": api_key, "units": units}

    response = requests.get(url, params=params, timeout=15)

    if response.status_code == 401:
        raise Exception("Authentication failed: Invalid API key (401 Unauthorized)")
    if response.status_code == 404:
        msg = response.json().get("message", "location not found")
        raise Exception(f"404 error: {msg}")

    data = response.json()

    # Safe gets
    main = data.get("main", {})
    weather_list = data.get("weather", [])
    desc = weather_list[0].get("description") if weather_list else "unknown"

    result = {
        "location": location,
        "units": units,
        "description": desc,
        "temperature": round(main.get("temp", 0.0), 2),
        "feels_like": round(main.get("feels_like", 0.0), 2),
        "temp_min": round(main.get("temp_min", 0.0), 2),
        "temp_max": round(main.get("temp_max", 0.0), 2),
        "humidity": round(main.get("humidity", 0.0), 2),
    }
    return result


# -------------------------
# OpenAI tool definition
# -------------------------
weather_tool = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather for a given location (city/region/country).",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location like 'Syracuse, NY, US' or 'Lima, Peru'. If missing/empty, default to Syracuse, NY.",
                    },
                    "units": {
                        "type": "string",
                        "enum": ["imperial", "metric"],
                        "description": "imperial = Fahrenheit, metric = Celsius",
                    },
                },
                "required": ["location"],
            },
        },
    }
]


# -------------------------
# Streamlit App UI
# -------------------------
st.title("Lab 5 — Weather Advice Bot (Tool Calling)")

st.write(
    "Type a city (or ask generally). The bot will call the weather tool only when needed, "
    "then give outfit + outdoor activity suggestions."
)

# User inputs
default_location = "Syracuse, NY, US"
user_location = st.text_input("Default location (used if you don't provide one)", default_location)
units = st.selectbox("Units", ["imperial", "metric"])

user_prompt = st.text_area(
    "What do you want to know?",
    "What should I wear today and what outdoor activities are good?",
)

# Required tests (button)
with st.expander("Run required tests (Syracuse, NY, US + Lima, Peru)"):
    if st.button("Run weather function tests"):
        try:
            syr = get_current_weather("Syracuse, NY, US", units)
            lima = get_current_weather("Lima, Peru", units)
            st.write("✅ Syracuse test:", syr)
            st.write("✅ Lima test:", lima)
        except Exception as e:
            st.error(f"Test failed: {e}")

# Main button
if st.button("Get advice"):
    # OpenAI client
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # 1) First call: allow tool calling (tool_choice='auto')
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful weather advice assistant. "
                "If you need current weather, call the tool get_current_weather. "
                "After weather is available, give: (1) clothing suggestions and (2) outdoor activity ideas."
            ),
        },
        {
            "role": "user",
            "content": (
                f"User default location is: {user_location}. Units: {units}.\n\n"
                f"User request: {user_prompt}\n\n"
                "IMPORTANT: If the user did not specify a location, use the default location."
            ),
        },
    ]

    try:
        first = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=weather_tool,
            tool_choice="auto",
        )

        assistant_msg = first.choices[0].message

        # If the model asked to call the tool, do it, then make the 2nd call
        if assistant_msg.tool_calls:
            # Add assistant tool-call message
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_msg.content,
                    "tool_calls": assistant_msg.tool_calls,
                }
            )

            # Execute each tool call
            for tc in assistant_msg.tool_calls:
                fn_name = tc.function.name
                args = json.loads(tc.function.arguments or "{}")

                # Default location rule
                loc = (args.get("location") or "").strip()
                if not loc:
                    loc = user_location or default_location

                # Units rule
                tool_units = args.get("units", units)

                if fn_name == "get_current_weather":
                    weather_data = get_current_weather(loc, tool_units)
                else:
                    weather_data = {"error": f"Unknown tool: {fn_name}"}

                # Add tool result message
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(weather_data),
                    }
                )

            # 2) Second call: now that weather is known, ask for final advice
            second = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
            )

            final_text = second.choices[0].message.content
            st.subheader("Advice")
            st.write(final_text)

            # Optional: show weather data used
            st.subheader("Weather used")
            # last tool message content is json weather; show all tool outputs
            for m in messages:
                if m["role"] == "tool":
                    st.json(json.loads(m["content"]))

        else:
            # If the model didn't need the tool, just show its response
            st.subheader("Advice")
            st.write(assistant_msg.content)

    except Exception as e:
        st.error(f"Something went wrong: {e}")