"""
Sales EVA Testing Framework

A comprehensive testing framework for evaluating Sales Virtual Advisor systems.
"""

__version__ = "1.0.0"
__author__ = "Sales EVA Testing Team"

from src.tester import SalesEVATester
from src.api_client import APIClient, TestDataGenerator

__all__ = ["SalesEVATester", "APIClient", "TestDataGenerator"]