from sentence_transformers import SentenceTransformer, util
from scrapers.models import Post

def filter_similar_posts(new_posts: list[Post], existing_posts: list[Post], threshold: float = 0.8) -> list[Post]:
    if len(existing_posts) == 0:
        return new_posts

    model = SentenceTransformer('all-MiniLM-L6-v2')

    existing_titles = [post.title for post in existing_posts]
    existing_descriptions = [post.desc for post in existing_posts]

    existing_embeddings = model.encode(existing_titles + existing_descriptions, convert_to_tensor=True)

    filtered_posts = []
    for post in new_posts:
        title_embedding = model.encode(post.title, convert_to_tensor=True)
        description_embedding = model.encode(post.desc, convert_to_tensor=True)

        title_similarities = util.pytorch_cos_sim(title_embedding, existing_embeddings[:len(existing_titles)])
        description_similarities = util.pytorch_cos_sim(description_embedding, existing_embeddings[len(existing_titles):])

        if title_similarities.max() < threshold and description_similarities.max() < threshold:
            filtered_posts.append(post)

    return filtered_posts