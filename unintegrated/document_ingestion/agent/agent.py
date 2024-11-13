from typing import Optional, Dict, Any, Union, List, TypeVar, overload
import torch
from transformers import AutoModel, AutoTokenizer, PreTrainedModel, PreTrainedTokenizer
from transformers.modeling_outputs import BaseModelOutput

T = TypeVar('T', bound='LanguageAgent')

class LanguageAgent:
  def __init__(
    self: T,
    model_name: str,
    device: Optional[str] = None,
    **kwargs: Any
  ) -> None:
    """
    Initialize the base language agent.
    
    Args:
      model_name: Name of the pretrained model to load
      device: Device to run the model on. If None, automatically selects cuda if available
      **kwargs: Additional arguments to pass to the model initialization
    """
    self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    self.model_name = model_name
    
    # Load tokenizer and model with explicit typing
    self.tokenizer: PreTrainedTokenizer = AutoTokenizer.from_pretrained(model_name)
    self.model: PreTrainedModel = AutoModel.from_pretrained(model_name, **kwargs)
    self.model.to(self.device)
    
  @overload
  def encode(
    self: T,
    text: str,
    max_length: Optional[int] = None,
    padding: bool = True,
    truncation: bool = True,
    return_tensors: str = "pt",
    **kwargs: Any
  ) -> Dict[str, torch.Tensor]: ...
  
  @overload
  def encode(
    self: T,
    text: List[str],
    max_length: Optional[int] = None,
    padding: bool = True,
    truncation: bool = True,
    return_tensors: str = "pt",
    **kwargs: Any
  ) -> Dict[str, torch.Tensor]: ...
  
  def encode(
    self: T,
    text: Union[str, List[str]],
    max_length: Optional[int] = None,
    padding: bool = True,
    truncation: bool = True,
    return_tensors: str = "pt",
    **kwargs: Any
  ) -> Dict[str, torch.Tensor]:
    """
    Encode input text using the tokenizer.
    
    Args:
      text: Input text or list of texts to encode
      max_length: Maximum length of the encoded sequence
      padding: Whether to pad sequences
      truncation: Whether to truncate sequences
      return_tensors: Type of tensors to return
      **kwargs: Additional arguments to pass to the tokenizer
        
    Returns:
      Dictionary containing the encoded inputs moved to the correct device
    """
    encoded = self.tokenizer(
      text,
      max_length=max_length,
      padding=padding,
      truncation=truncation,
      return_tensors=return_tensors,
      **kwargs
    )
    return {k: v.to(self.device) for k, v in encoded.items()}
  
  @overload
  def decode(
    self: T,
    token_ids: torch.Tensor,
    skip_special_tokens: bool = True,
    **kwargs: Any
  ) -> str: ...
  
  @overload
  def decode(
    self: T,
    token_ids: List[torch.Tensor],
    skip_special_tokens: bool = True,
    **kwargs: Any
  ) -> List[str]: ...
  
  def decode(
    self: T,
    token_ids: Union[torch.Tensor, List[torch.Tensor]],
    skip_special_tokens: bool = True,
    **kwargs: Any
  ) -> Union[str, List[str]]:
    """
    Decode token IDs back to text.
    
    Args:
      token_ids: Tensor or list of tensors of token IDs to decode
      skip_special_tokens: Whether to remove special tokens in the decoding
      **kwargs: Additional arguments to pass to the tokenizer
        
    Returns:
      Decoded text or list of texts
    """
    if isinstance(token_ids, list):
      return [
        self.tokenizer.decode(ids, skip_special_tokens=skip_special_tokens, **kwargs)
        for ids in token_ids
      ]
    return self.tokenizer.decode(
      token_ids,
      skip_special_tokens=skip_special_tokens,
      **kwargs
    )
  
  def __call__(self, *args: Any, **kwargs: Any) -> Any:
    """
    Process input through the model.
    To be implemented by derived classes.
    """
    raise NotImplementedError("Derived classes must implement __call__")


from transformers import AutoModelForSeq2SeqLM
from dataclasses import dataclass
from transformers.generation import GenerationConfig

@dataclass
class SummarizerConfig:
  max_length: int = 2048
  num_beams: int = 4
  summary_length: str = "brief"
  temperature: float = 1.0
  do_sample: bool = False
  early_stopping: bool = True
  no_repeat_ngram_size: int = 3
  length_penalty: float = 1.0

class Summarizer(LanguageAgent):
  def __init__(
    self,
    model_name: str = "utrobinmv/t5_summary_en_ru_zh_base_2048",
    config: Optional[SummarizerConfig] = None,
    device: Optional[str] = None,
    **kwargs: Any
  ) -> None:
    """
    Initialize the summarizer.
    
    Args:
      model_name: Name of the pretrained model to load
      config: Configuration for the summarizer
      device: Device to run the model on
      **kwargs: Additional arguments to pass to the model initialization
    """
    super().__init__(model_name, device, **kwargs)
    
    # Override the model with the correct type for summarization
    self.model: PreTrainedModel = AutoModelForSeq2SeqLM.from_pretrained(
      model_name,
      **kwargs
    )
    self.model.to(self.device)
    
    # Set configuration
    self.config = config or SummarizerConfig()
    
    # Set up generation config
    self.generation_config = GenerationConfig(
      max_length=self.config.max_length,
      num_beams=self.config.num_beams,
      temperature=self.config.temperature,
      do_sample=self.config.do_sample,
      early_stopping=self.config.early_stopping,
      no_repeat_ngram_size=self.config.no_repeat_ngram_size,
      length_penalty=self.config.length_penalty
    )
  
  @torch.no_grad()
  def __call__(self,
    text: Union[str, List[str]],
    generation_config: Optional[GenerationConfig] = None,
    **kwargs: Any
  ) -> Union[str, List[str]]:
    """
    Generate a summary for the input text.
    
    Args:
      text: Text or list of texts to summarize
      generation_config: Optional custom generation configuration
      **kwargs: Additional arguments to pass to the generation
        
    Returns:
      Generated summary or list of summaries
    """
    # Add text prefix
    prefix = f"summary {self.config.summary_length}: "
    # Encode the input text
    inputs = self.encode(prefix+text, return_tensors="pt")
    
    # Use provided generation config or default
    config = generation_config or self.generation_config
    
    # Generate summary
    outputs = self.model.generate(
      **inputs,
      generation_config=config,
      **kwargs
    )
    
    # Decode and return the summary
    if isinstance(text, list):
      return [self.decode(output) for output in outputs]
    return self.decode(outputs[0])
  
  def update_config(self, **kwargs: Any) -> None:
    """
    Update the summarizer configuration.
    
    Args:
      **kwargs: Configuration parameters to update
    """
    for key, value in kwargs.items():
      if hasattr(self.config, key):
        setattr(self.config, key, value)
    
    # Update generation config
    self.generation_config = GenerationConfig(**vars(self.config))


from typing import List, Dict, Optional, Union, Tuple
import torch
import numpy as np
from dataclasses import dataclass

@dataclass
class CategorizerConfig:
  model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
  threshold: float = 0.0  # Minimum similarity threshold
  top_k: int = 1  # Number of top categories to return

class Categorizer(LanguageAgent):
  def __init__(
    self,
    categories: List[str],
    config: Optional[CategorizerConfig] = None,
    device: Optional[str] = None,
    **kwargs: Any
  ) -> None:
    """
    Initialize the categorizer.
    
    Args:
      categories: List of category names to classify against
      config: Configuration for the categorizer
      device: Device to run the model on
      **kwargs: Additional arguments to pass to the model initialization
    """
    self.config = config or CategorizerConfig()
    super().__init__(self.config.model_name, device, **kwargs)
    
    self.categories = categories
    # Pre-compute category embeddings
    self._compute_category_embeddings()
  
  def _compute_category_embeddings(self) -> None:
    """
    Compute and store embeddings for all categories.
    """
    with torch.no_grad():
      inputs = self.encode(self.categories, padding=True, truncation=True)
      outputs = self.model(**inputs)
      # Use mean pooling of the last hidden state
      self.category_embeddings = outputs.last_hidden_state.mean(dim=1)
  
  def _compute_similarities(self, text_embedding: torch.Tensor) -> torch.Tensor:
    """
    Compute cosine similarities between input embedding and category embeddings.
    
    Args:
      text_embedding: Embedding tensor for input text
    
    Returns:
      Tensor of similarity scores
    """
    # Compute cosine similarity
    similarities = torch.nn.functional.cosine_similarity(
      text_embedding.unsqueeze(1),
      self.category_embeddings.unsqueeze(0),
      dim=2
    )
    return similarities
  
  def get_top_categories(self, similarities: torch.Tensor, k: Optional[int] = None) -> List[Tuple[str, float]]:
    """
    Get top k categories and their similarity scores.
    
    Args:
      similarities: Tensor of similarity scores
      k: Number of top categories to return (defaults to config.top_k)
    
    Returns:
      List of (category, score) tuples sorted by score
    """
    k = k or self.config.top_k
    top_k = min(k, len(self.categories))
    
    # Get top k indices and scores
    scores, indices = similarities.topk(top_k)
    
    # Convert to list of (category, score) tuples
    return [
      (self.categories[idx], score.item())
      for idx, score in zip(indices, scores)
    ]
  
  @torch.no_grad()
  def __call__(
    self,
    text: Union[str, List[str]],
    threshold: Optional[float] = None,
    top_k: Optional[int] = None,
    return_scores: bool = True
  ) -> Union[List[str], List[Tuple[str, float]], List[List[str]], List[List[Tuple[str, float]]]]:
    """
    Categorize input text(s).
    
    Args:
      text: Input text or list of texts to categorize
      threshold: Optional minimum similarity threshold (overrides config)
      top_k: Optional number of top categories to return (overrides config)
      return_scores: Whether to return similarity scores with categories
    
    Returns:
      If single text input:
        - List of top category names if return_scores=False
        - List of (category, score) tuples if return_scores=True
      If list of texts:
        - List of lists of category names if return_scores=False
        - List of lists of (category, score) tuples if return_scores=True
    """
    threshold = threshold if threshold is not None else self.config.threshold
    is_single = isinstance(text, str)
    texts = [text] if is_single else text
    
    # Encode input texts
    inputs = self.encode(texts, padding=True, truncation=True)
    
    # Get text embeddings
    outputs = self.model(**inputs)
    text_embeddings = outputs.last_hidden_state.mean(dim=1)
    
    # Compute similarities for all texts
    all_similarities = self._compute_similarities(text_embeddings)
    
    # Process each text's similarities
    results = []
    for similarities in all_similarities:
      # Filter by threshold
      mask = similarities >= threshold
      filtered_similarities = similarities[mask]
      filtered_categories = [cat for cat, m in zip(self.categories, mask) if m]
      
      # Get top categories
      if filtered_similarities.numel() > 0:
        top_cats = self.get_top_categories(filtered_similarities, top_k)
      else:
        top_cats = []
      
      results.append(
        top_cats if return_scores else [cat for cat, _ in top_cats]
      )
    
    return results[0] if is_single else results
  
  def update_categories(self, categories: List[str]) -> None:
    """
    Update the list of categories and recompute embeddings.
    
    Args:
      categories: New list of categories
    """
    self.categories = categories
    self._compute_category_embeddings()
  
  def add_categories(self, new_categories: List[str]) -> None:
    """
    Add new categories to the existing list and update embeddings.
    
    Args:
      new_categories: List of new categories to add
    """
    self.categories.extend(new_categories)
    self._compute_category_embeddings()

# Example usage:
if __name__ == "__main__":
  categories = [
    "Finance Folder",
    "Operations Folder",
    "Marketing Folder",
    "Marketing/Competitive Intelligence Folder",
    "Marketing/Advertising Folder",
    "Marketing/Brand Folder",
    "Operations/Supply Chain Folder",
    "Operations/Invoices Folder"
  ]
  
  config = CategorizerConfig(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    threshold=0.1,
    top_k=3
  )
  
  categorizer = Categorizer(categories, config=config)
  
  # Single text categorization
  text = "Proposal for Equity Investment in Advance Chemicals"
  results = categorizer(text, return_scores=True)
  print("\nSingle text categorization:")
  for category, score in results:
    print(f"{category}: {score:.4f}")
  
  # Multiple texts categorization
  texts = [
    "Proposal for Equity Investment in Advance Chemicals",
    "New Marketing Campaign for Q4",
    "Invoice Processing Guidelines Update"
  ]
  results = categorizer(texts, return_scores=True)
  print("\nMultiple texts categorization:")
  for text, cats in zip(texts, results):
    print(f"\nText: {text}")
    for category, score in cats:
      print(f"{category}: {score:.4f}")