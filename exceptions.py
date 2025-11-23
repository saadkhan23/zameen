#!/usr/bin/env python3
"""
exceptions.py

Custom exception classes for the Zameen real estate analysis project.

These exceptions provide semantic meaning to errors and enable targeted
exception handling with clear recovery strategies.

Exception Hierarchy:
    Exception
    └── ZameenError (Base exception for all Zameen operations)
        ├── ScraperError (Web scraping failures)
        ├── DataParsingError (Data parsing/extraction failures)
        ├── InvalidPropertyError (Invalid or malformed property data)
        └── ValidationError (Data validation failures)
"""


class ZameenError(Exception):
    """
    Base exception for all Zameen operations.

    Use this as the parent class for all custom Zameen exceptions.
    Allows catching all Zameen-specific errors while letting system
    errors (e.g., MemoryError) bubble up naturally.
    """

    pass


class ScraperError(ZameenError):
    """
    Exception raised during web scraping operations.

    Indicates an error occurred while scraping property listings from
    Zameen.com using Playwright or other scraping methods.

    Examples:
        - Network timeout during page load
        - Failed to extract JSON data from page
        - Unexpected HTML structure
    """

    pass


class DataParsingError(ZameenError):
    """
    Exception raised when parsing property data fails.

    Indicates an error occurred while extracting or parsing data from
    Excel files, JSON responses, or other data sources.

    Examples:
        - Missing required column in Excel sheet
        - Invalid data type in price/size fields
        - Cannot convert string to numeric value
    """

    pass


class InvalidPropertyError(ZameenError):
    """
    Exception raised when property data is invalid or malformed.

    Indicates that property data exists but contains invalid values
    that don't meet business rules or data quality standards.

    Examples:
        - Price is negative or zero
        - Size is impossibly large or small
        - Required fields are missing
        - Data consistency check failed
    """

    pass


class ValidationError(ZameenError):
    """
    Exception raised when data validation fails.

    Indicates that input data or configuration doesn't meet validation
    requirements before processing can continue.

    Examples:
        - Invalid location name format
        - Location ID out of expected range
        - Configuration parameter is invalid
        - DataFrame structure doesn't match expected schema
    """

    pass
