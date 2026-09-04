from google import genai

client = genai.Client()

response = client.interactions.create(
    model="gemini-3.6-flash",
    input="Say hello to my Polar Outreach Assistant in one short sentence."
)

print(response.output_text)