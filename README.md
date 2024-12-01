# LLM infused website analyzer 
A simple usecase for genAI, automating the process of client/competitor research. 
Running on Flask. Once the program is running, access on localhost:5000.

## Requirements
import necessary python libraries and ensure Ollama is running and Llama3.2:3b is installed.

When I worked as a marketing data analyst it was a time consuming task to write reports on competitors.
Leveraging LLMs and webscraping, we can automate this process.

## Current implementation
Using Ollama and Llama3.2:3b (excellent for fast summarization tasks), we have a report generating web scraper to automate basic market research tasks.

## Planned features
- batch processing of websites, saving reports to a CSV
- structured output, to facilitate creation of a database of competitors
- LLM as a judge to remove links to irrelevant pages such as privacy policy pages
- containerise the package for easy installation on any machine (need to see how local LLMs work with this)
- include a competitor analysis mode and potential client vetting (simple toggle to switch between hardcoded prompts
- refinements and improvements to the prompt (one shot prompt by including example)
