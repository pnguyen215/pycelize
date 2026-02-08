"""
Unit tests for IntentClassifier
"""

import pytest
from app.chat.intent_classifier import IntentClassifier, IntentType


class TestIntentClassifier:
    """Test suite for IntentClassifier."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.classifier = IntentClassifier()
    
    def test_initialization(self):
        """Test classifier initialization."""
        assert self.classifier is not None
        operations = self.classifier.get_supported_operations()
        assert len(operations) > 0
        assert "extract_columns" in operations
    
    def test_extract_columns_intent(self):
        """Test extract columns intent classification."""
        # Test direct message
        intent = self.classifier.classify("extract columns: name, email, phone")
        assert intent.intent_type == IntentType.EXTRACT_COLUMNS
        assert intent.confidence > 0.5
        assert len(intent.suggested_operations) > 0
        assert "name" in intent.extracted_params.get("columns", [])
        
        # Test alternative phrasing
        intent2 = self.classifier.classify("get the name and email columns")
        assert intent2.intent_type == IntentType.EXTRACT_COLUMNS
        
        # Test with keywords
        intent3 = self.classifier.classify("select customer_id and amount fields")
        assert intent3.intent_type == IntentType.EXTRACT_COLUMNS
    
    def test_convert_format_intent(self):
        """Test convert format intent classification."""
        # Test CSV to Excel
        intent = self.classifier.classify("convert to Excel")
        assert intent.intent_type == IntentType.CONVERT_FORMAT
        assert intent.confidence > 0.5
        
        # Test JSON conversion
        intent2 = self.classifier.classify("export as JSON")
        assert intent2.intent_type == IntentType.CONVERT_FORMAT
        assert len(intent2.suggested_operations) > 0
    
    def test_normalize_data_intent(self):
        """Test normalize data intent classification."""
        # Test normalization request
        intent = self.classifier.classify("normalize data - uppercase and trim")
        assert intent.intent_type == IntentType.NORMALIZE_DATA
        assert intent.confidence > 0.5
        
        # Test clean data
        intent2 = self.classifier.classify("clean the data")
        assert intent2.intent_type == IntentType.NORMALIZE_DATA
        
        # Test standardize
        intent3 = self.classifier.classify("standardize phone numbers")
        assert intent3.intent_type == IntentType.NORMALIZE_DATA
    
    def test_generate_sql_intent(self):
        """Test generate SQL intent classification."""
        # Test SQL generation
        intent = self.classifier.classify("generate SQL for table users")
        assert intent.intent_type == IntentType.GENERATE_SQL
        assert intent.confidence > 0.5
        
        # Test insert statements
        intent2 = self.classifier.classify("create insert statements")
        assert intent2.intent_type == IntentType.GENERATE_SQL
    
    def test_generate_json_intent(self):
        """Test generate JSON intent classification."""
        intent = self.classifier.classify("generate JSON")
        assert intent.intent_type == IntentType.GENERATE_JSON
        assert intent.confidence > 0.5
        
        intent2 = self.classifier.classify("convert to JSON format")
        assert intent2.intent_type == IntentType.GENERATE_JSON
    
    def test_search_filter_intent(self):
        """Test search/filter intent classification."""
        intent = self.classifier.classify("search for active customers")
        assert intent.intent_type == IntentType.SEARCH_FILTER
        assert intent.confidence > 0.5
        
        intent2 = self.classifier.classify("filter data where amount > 1000")
        assert intent2.intent_type == IntentType.SEARCH_FILTER
    
    def test_bind_data_intent(self):
        """Test bind data intent classification."""
        intent = self.classifier.classify("bind data from another file")
        assert intent.intent_type == IntentType.BIND_DATA
        assert intent.confidence > 0.5
        
        intent2 = self.classifier.classify("merge with customer_info.xlsx")
        assert intent2.intent_type == IntentType.BIND_DATA
    
    def test_map_columns_intent(self):
        """Test map columns intent classification."""
        intent = self.classifier.classify("rename columns")
        assert intent.intent_type == IntentType.MAP_COLUMNS
        assert intent.confidence > 0.5
        
        intent2 = self.classifier.classify("map column names")
        assert intent2.intent_type == IntentType.MAP_COLUMNS
    
    def test_unknown_intent(self):
        """Test unknown intent classification."""
        intent = self.classifier.classify("do something random")
        assert intent.intent_type == IntentType.UNKNOWN
        assert intent.confidence == 0.0
    
    def test_column_extraction(self):
        """Test column name extraction from message."""
        # Test direct format
        columns = self.classifier._extract_column_names("columns: name, email, phone")
        assert "name" in columns
        assert "email" in columns
        assert "phone" in columns
        
        # Test extract format
        columns2 = self.classifier._extract_column_names("extract customer_id, amount from data")
        assert "customer_id" in columns2
        assert "amount" in columns2
    
    def test_confidence_scoring(self):
        """Test confidence scoring mechanism."""
        # High confidence with direct keywords
        intent1 = self.classifier.classify("extract columns: name, email")
        
        # Lower confidence with indirect phrasing
        intent2 = self.classifier.classify("I need some columns")
        
        # Unknown should have 0 confidence
        intent3 = self.classifier.classify("xyz abc 123")
        
        assert intent1.confidence > intent2.confidence
        assert intent3.confidence == 0.0
    
    def test_suggested_operations_structure(self):
        """Test suggested operations have correct structure."""
        intent = self.classifier.classify("extract columns: name, email")
        
        assert len(intent.suggested_operations) > 0
        operation = intent.suggested_operations[0]
        
        assert "operation" in operation
        assert "arguments" in operation
        assert "description" in operation
    
    def test_explanation_generation(self):
        """Test explanation generation for intents."""
        intent = self.classifier.classify("convert to JSON")
        
        assert intent.explanation is not None
        assert len(intent.explanation) > 0
        assert isinstance(intent.explanation, str)
    
    def test_context_usage(self):
        """Test context usage in classification."""
        # Test with CSV file context
        intent_csv = self.classifier.classify(
            "convert to Excel",
            context={"file_type": "csv"}
        )
        
        # Test with Excel file context
        intent_excel = self.classifier.classify(
            "convert to CSV",
            context={"file_type": "xlsx"}
        )
        
        assert intent_csv.intent_type == IntentType.CONVERT_FORMAT
        assert intent_excel.intent_type == IntentType.CONVERT_FORMAT
    
    def test_case_insensitivity(self):
        """Test that classification is case-insensitive."""
        intent1 = self.classifier.classify("EXTRACT COLUMNS: NAME, EMAIL")
        intent2 = self.classifier.classify("extract columns: name, email")
        intent3 = self.classifier.classify("Extract Columns: Name, Email")
        
        assert intent1.intent_type == intent2.intent_type == intent3.intent_type
    
    def test_parameter_extraction_duplicates(self):
        """Test parameter extraction for duplicate removal."""
        intent = self.classifier.classify("extract unique values from column")
        
        params = intent.extracted_params
        assert "remove_duplicates" in params
        assert params["remove_duplicates"] is True
    
    def test_parameter_extraction_case(self):
        """Test parameter extraction for case transformation."""
        intent1 = self.classifier.classify("convert to uppercase")
        assert intent1.extracted_params.get("case") == "upper"
        
        intent2 = self.classifier.classify("convert to lowercase")
        assert intent2.extracted_params.get("case") == "lower"
    
    def test_multiple_keywords(self):
        """Test classification with multiple matching keywords."""
        # This should strongly match extract columns
        intent = self.classifier.classify("extract and select columns: name, email")
        
        assert intent.intent_type == IntentType.EXTRACT_COLUMNS
        assert intent.confidence > 0.7
    
    def test_get_supported_operations(self):
        """Test getting supported operations."""
        operations = self.classifier.get_supported_operations()
        
        assert isinstance(operations, dict)
        assert len(operations) >= 8  # Should have at least 8 intent types
        
        # Check specific operations
        assert "extract_columns" in operations
        assert "convert_format" in operations
        assert "normalize_data" in operations


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
