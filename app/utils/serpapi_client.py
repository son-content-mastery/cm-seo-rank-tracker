import requests
import time
import logging
from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple
from app.config import Config

logger = logging.getLogger(__name__)


class SerpAPIClient:
    """Client for interacting with SerpAPI to get search results"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search"
        self.rate_limit_delay = Config.SERPAPI_RATE_LIMIT
    
    def search_google(self, keyword: str, location: str = 'United States') -> Dict:
        """
        Search Google for a keyword and return SERP results
        
        Args:
            keyword: The search keyword
            location: Geographic location for the search
            
        Returns:
            Dict containing search results
        """
        params = {
            'engine': 'google',
            'q': keyword,
            'location': location,
            'hl': Config.SEARCH_CONFIG['language'],
            'gl': Config.SEARCH_CONFIG['country'],
            'num': Config.SEARCH_CONFIG['num_results'],
            'safe': Config.SEARCH_CONFIG['safe'],
            'api_key': self.api_key
        }
        
        try:
            logger.info(f"Searching for keyword: {keyword}")
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Apply rate limiting
            time.sleep(self.rate_limit_delay)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching for keyword '{keyword}': {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error searching for keyword '{keyword}': {e}")
            return {}
    
    def find_domain_position(self, serp_results: Dict, target_domain: str) -> Tuple[Optional[int], Optional[Dict]]:
        """
        Find the position of a target domain in search results
        
        Args:
            serp_results: Raw SERP results from SerpAPI
            target_domain: Domain to search for (e.g., 'example.com')
            
        Returns:
            Tuple of (position, result_dict) or (None, None) if not found
        """
        organic_results = serp_results.get('organic_results', [])
        
        # Clean target domain (remove www, protocols, etc.)
        clean_target = self._clean_domain(target_domain)
        
        for i, result in enumerate(organic_results, 1):
            result_url = result.get('link', '')
            if result_url:
                result_domain = self._clean_domain(result_url)
                if clean_target.lower() in result_domain.lower():
                    logger.info(f"Found {target_domain} at position {i}")
                    return i, result
        
        logger.info(f"Domain {target_domain} not found in top {len(organic_results)} results")
        return None, None
    
    def extract_serp_features(self, serp_results: Dict) -> Dict:
        """
        Extract additional SERP features that might be useful
        
        Args:
            serp_results: Raw SERP results from SerpAPI
            
        Returns:
            Dict containing extracted features
        """
        features = {
            'total_results': serp_results.get('search_information', {}).get('total_results'),
            'time_taken': serp_results.get('search_information', {}).get('time_taken_displayed'),
            'featured_snippet': bool(serp_results.get('featured_snippet')),
            'knowledge_graph': bool(serp_results.get('knowledge_graph')),
            'local_results': bool(serp_results.get('local_results')),
            'ads_count': len(serp_results.get('ads', [])),
            'organic_count': len(serp_results.get('organic_results', [])),
            'related_searches': len(serp_results.get('related_searches', [])),
            'people_also_ask': len(serp_results.get('people_also_ask', []))
        }
        
        return features
    
    def _clean_domain(self, url_or_domain: str) -> str:
        """
        Clean and normalize a domain for comparison
        
        Args:
            url_or_domain: URL or domain to clean
            
        Returns:
            Cleaned domain string
        """
        if not url_or_domain:
            return ""
            
        # If it looks like a URL, parse it
        if url_or_domain.startswith(('http://', 'https://')):
            parsed = urlparse(url_or_domain)
            domain = parsed.netloc
        else:
            domain = url_or_domain
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # Remove trailing slashes and convert to lowercase
        return domain.rstrip('/').lower()
    
    def rate_limit_handler(self):
        """Handle rate limiting between requests"""
        time.sleep(self.rate_limit_delay)


def get_keyword_ranking(keyword: str, target_domain: str, api_key: str) -> Dict:
    """
    Get ranking information for a specific keyword and domain
    
    Args:
        keyword: Search keyword
        target_domain: Domain to check ranking for
        api_key: SerpAPI key
        
    Returns:
        Dict containing ranking information
    """
    client = SerpAPIClient(api_key)
    
    # Search for the keyword
    search_results = client.search_google(keyword)
    
    if not search_results:
        return {
            'keyword': keyword,
            'domain': target_domain,
            'position': None,
            'found_in_top_100': False,
            'url': None,
            'title': None,
            'serp_features': {},
            'error': 'Failed to get search results'
        }
    
    # Find domain position
    position, result_data = client.find_domain_position(search_results, target_domain)
    
    # Extract SERP features
    serp_features = client.extract_serp_features(search_results)
    
    ranking_data = {
        'keyword': keyword,
        'domain': target_domain,
        'position': position,
        'found_in_top_100': position is not None,
        'url': result_data.get('link') if result_data else None,
        'title': result_data.get('title') if result_data else None,
        'serp_features': serp_features,
        'error': None
    }
    
    return ranking_data


def batch_check_keywords(keywords: List[str], target_domain: str, api_key: str) -> List[Dict]:
    """
    Check rankings for multiple keywords with rate limiting
    
    Args:
        keywords: List of keywords to check
        target_domain: Domain to check rankings for
        api_key: SerpAPI key
        
    Returns:
        List of ranking data dictionaries
    """
    results = []
    client = SerpAPIClient(api_key)
    
    for i, keyword in enumerate(keywords):
        logger.info(f"Checking keyword {i+1}/{len(keywords)}: {keyword}")
        
        try:
            ranking_data = get_keyword_ranking(keyword, target_domain, api_key)
            results.append(ranking_data)
            
            # Rate limiting between requests (except for the last one)
            if i < len(keywords) - 1:
                client.rate_limit_handler()
                
        except Exception as e:
            logger.error(f"Error checking keyword '{keyword}': {e}")
            results.append({
                'keyword': keyword,
                'domain': target_domain,
                'position': None,
                'found_in_top_100': False,
                'url': None,
                'title': None,
                'serp_features': {},
                'error': str(e)
            })
    
    return results