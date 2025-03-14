from transformers import AutoModel, AutoTokenizer
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Device: ",device)

# model = AutoModel.from_pretrained("openai/clip-vit-base-patch16").to(device)
# processor = AutoImageProcessor.from_pretrained("openai/clip-vit-base-patch16")
# tokenizer = AutoTokenizer.from_pretrained("openai/clip-vit-base-patch16")

model = AutoModel.from_pretrained(
    "BAAI/bge-large-en-v1.5",
    cache_dir=r"E:\RAG\huggingface_cache",
    device_map="auto")

tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-large-en-v1.5",cache_dir=r"E:\RAG\huggingface_cache")

def embedding_the_chunks(chunks):
    chunk_embeddings = []
    for chunk in chunks:
        inputs = tokenizer(chunk, return_tensors="pt", padding=True, truncation=True).to(device)
        with torch.no_grad():
            text_outputs = model(**inputs)  
            sentence_embeddings = text_outputs[0][:, 0]
        sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)

            #normalized_embeddings = text_outputs / text_outputs.norm(dim=-1, keepdim=True)
        embeddings = sentence_embeddings.squeeze(0).cpu().tolist()  # Flatten
        chunk_embeddings.append(embeddings)
            
# # Convert embeddings to a Python list or numpy array
# embeddings = normalized_embeddings.squeeze(0).cpu().tolist()

    # Print the embedding details
    print("Embedding size:", len(embeddings))
    print("Chunk_Embeddings:", len(chunk_embeddings))

    return chunk_embeddings

