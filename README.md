# Haiku Agent Project

This project contains a multi-component system for generating, validating, and storing haikus. It is built using the Google Agent Development Kit (ADK) and demonstrates a microservices-style architecture for agentic applications.

## Project Components

This repository is a monorepo containing the following services:

*   **`haiku-app/`**: The main, user-facing application. This is a ReAct agent that orchestrates the process of creating and validating haikus. For more information, see the [`haiku-app/README.md`](haiku-app/README.md).
*   **`a2a_validator/`**: A haiku validation service. This agent exposes an Agent-to-Agent (A2A) endpoint that the `haiku-app` can call to validate the structure of a haiku. For more information, see the [`a2a_validator/README.md`](a2a_validator/README.md).
*   **`mcp-haiku-store/`**: A service for storing and retrieving haikus. This service uses FastMCP to expose a REST-like API for haiku management. For more information, see the [`mcp-haiku-store/README.md`](mcp-haiku-store/README.md).

## System Overview

The `haiku-app` is the entry point for user interaction. When a user asks for a haiku, the `haiku-app` will:

1.  Generate a haiku.
2.  Call the `a2a_validator` service to ensure the generated text is a valid haiku.
3.  Store the validated haiku using the `mcp-haiku-store` service.

## Getting Started

To get started with this project, it is recommended to explore each of the sub-projects in the order listed above. Each component can be run and deployed independently. Please refer to the individual `README.md` files in each sub-directory for detailed setup and usage instructions.
