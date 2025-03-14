from dotenv import load_dotenv
import google.generativeai as genai
import os  
from serpapi import GoogleSearch

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    raise ValueError("GEMINI_API_KEY is missing. Please check your .env file.")

generation_config = {
    "temperature": 0.4,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2000,
    "response_mime_type": "application/json",
}
model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=generation_config,
        )

def generate_blog(topic, tone="informative"):
    prompt = f"Write a {tone} blog post about {topic}. Keep it engaging and well-structured. The blog should be in the way of simpler understanding. Also introduce the blog by the real-life example."
    response = genai.GenerativeModel("gemini-2.0-flash").generate_content(prompt)
    return response.text


def format_blog(blog_text):
    prompt = f"""Reformat this blog with proper headings, subheadings, and bullet points:\n{blog_text} 
    return the contents as topic and content of the blog should be returned as a response in json format.
    the response be like example, title and contents as the attribute in the json."""
    response = model.generate_content(prompt)
    print("\n\nResponse:", response.text)
    return response.text

#make it as two member podcast.
def frame_image_Search(topic, blog_content):
    # prompt = f"Frame a query to search the image in google image search for the blog content, the image that should be presented will have the better understanding. Give one query to search image in google for the {topic} with the help of blog content {blog_content}, frame the suitable question to search the image."
    img_Search_prompt = f"""Frame a query to search the image in google image search for the blog content, 
                    the image that should be presented will have the better understanding. 
                    Give sigle one query to search image in google for the {topic} with the help of blog content {blog_content},
                    frame the suitable question to search the image should be query or a statement to search in the google search, not too big."""
    response = genai.GenerativeModel("gemini-2.0-flash").generate_content(img_Search_prompt)
    return response.text

def get_related_images(query):
    params = {
        "q": query,
        "tbm": "isch",  # Image search
        "api_key": SERPAPI_KEY
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    
    image_urls = [img["original"] for img in results.get("images_results", [])]
    return image_urls[:2]  # Return top 5 images

topic = "Topic on Importance Sampling under the On and Off policy in reinforcement learning"
blog_content = generate_blog(topic, tone="insightful")
print(blog_content)


formatted_blog = format_blog(blog_content)
filename = f"{topic}.txt"

with open(filename, "w", encoding="utf-8") as file:
    file.write(formatted_blog)
    
print(f"✅ Blog saved successfully as '{filename}'!")

print(formatted_blog)

imge_query = frame_image_Search(topic, blog_content)
print("Image_Query:", imge_query)

related_images = get_related_images(imge_query)
print(related_images)  
