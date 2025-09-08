import os
from typing import Dict, Any
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class OpenAIProvider:
    def __init__(self):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            from security.api_key_vault import APIKeyVault
            vault = APIKeyVault()
            self.api_key = vault.get_key('openai')
        
        if self.api_key:
            openai.api_key = self.api_key
        else:
            raise ValueError("OpenAI API key not configured")
    
    def generate_response(self, query: str, context: Dict[str, Any]) -> str:
        try:
            # Enhanced entrepreneur-focused system prompt
            system_prompt = """You are an AI business assistant for entrepreneurs using Westfall Assistant. You specialize in:
            - Business strategy and growth advice
            - Productivity optimization for busy entrepreneurs
            - Tailor Pack recommendations for specific business needs
            - Data-driven insights and actionable recommendations
            - Time management and business process optimization
            
            Always provide practical, actionable advice focused on business growth and efficiency."""
            
            # Prepare enhanced context message
            context_msg = f"Current window: {context.get('window', 'Unknown')}"
            
            # Add business context if available
            if context.get('business_context'):
                biz_ctx = context['business_context']
                context_msg += f"\nUser type: {biz_ctx.get('user_type', 'entrepreneur')}"
                
                if biz_ctx.get('business_profile'):
                    profile = biz_ctx['business_profile']
                    context_msg += f"\nBusiness: {profile.get('business_name', 'N/A')} ({profile.get('business_type', 'N/A')})"
                    context_msg += f"\nIndustry: {profile.get('industry', 'N/A')}"
                
                if biz_ctx.get('active_tailor_packs'):
                    pack_names = [pack['name'] for pack in biz_ctx['active_tailor_packs']]
                    context_msg += f"\nActive Tailor Packs: {', '.join(pack_names) if pack_names else 'None'}"
                
                if biz_ctx.get('available_tools'):
                    context_msg += f"\nAvailable business tools: {', '.join(biz_ctx['available_tools'])}"
            
            if context.get('data'):
                context_msg += f"\nWindow context: {context['data']}"
            
            # Enhanced query with business focus
            business_query = self._enhance_query_for_business(query, context.get('business_context', {}))
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{context_msg}\n\nEntrepreneur query: {business_query}"}
                ],
                max_tokens=600,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def _enhance_query_for_business(self, query: str, business_context: Dict) -> str:
        """Enhance user queries with business context and suggestions"""
        enhanced_query = query
        
        # Add business context to common queries
        business_keywords = {
            "revenue": "Consider monthly recurring revenue, customer lifetime value, and growth trends",
            "customers": "Focus on customer acquisition cost, retention rate, and satisfaction metrics", 
            "marketing": "Analyze campaign ROI, lead generation efficiency, and conversion rates",
            "productivity": "Look at time allocation, task automation opportunities, and workflow optimization",
            "growth": "Examine scalability factors, market expansion opportunities, and competitive advantages",
            "tailor pack": "Consider which Tailor Packs could automate tasks and boost efficiency"
        }
        
        # Add relevant business context
        for keyword, context_tip in business_keywords.items():
            if keyword in query.lower():
                enhanced_query += f" (Business context: {context_tip})"
                break
        
        # Suggest Tailor Packs if relevant
        if any(word in query.lower() for word in ["automate", "efficiency", "save time", "streamline"]):
            if not business_context.get('active_tailor_packs'):
                enhanced_query += " (Note: User has no active Tailor Packs - consider recommending relevant business automation packs)"
        
        return enhanced_query