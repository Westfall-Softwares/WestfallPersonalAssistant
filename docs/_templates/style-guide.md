---
title: "Documentation Style Guide"
description: "Writing standards and guidelines for Westfall Personal Assistant documentation"
category: "meta"
priority: 1
tags: ["style", "guide", "writing", "standards"]
last_updated: "2025-09-08"
---

# Documentation Style Guide

This guide defines the writing standards and style conventions for all Westfall Personal Assistant documentation.

## Writing Principles

### 1. Clarity First
- Use clear, concise language
- Avoid jargon without explanation
- Write for your audience's skill level
- Use active voice when possible

### 2. User-Focused
- Start with what the user wants to accomplish
- Provide context for why something is important
- Include practical examples
- Anticipate user questions

### 3. Consistency
- Use consistent terminology throughout
- Follow established patterns and templates
- Maintain uniform formatting
- Use the same style for similar content types

## Front Matter Standards

All documentation files must include front matter with these fields:

```yaml
---
title: "Page Title (50 characters max)"
description: "Brief description (160 characters max)"
category: "user|developer|installation|configuration|reference|meta"
priority: 10
tags: ["tag1", "tag2", "tag3"]
last_updated: "YYYY-MM-DD"
---
```

### Field Descriptions

- **title**: The page title, used in navigation and search
- **description**: Brief summary for search results and previews
- **category**: Primary content category for organization
- **priority**: Display order within category (1-99, lower = higher priority)
- **tags**: Keywords for search and categorization
- **last_updated**: Last modification date in ISO format

## Content Structure

### Page Organization

1. **Title (H1)** - One per page, matches front matter title
2. **Introduction** - Brief overview of the content
3. **Main Sections (H2)** - Logical content divisions
4. **Subsections (H3-H6)** - Hierarchical content organization
5. **Related Links** - Cross-references to other documentation

### Section Guidelines

#### Overview Sections
- Explain what the reader will learn
- List prerequisites if any
- Provide context for the information

#### Step-by-Step Instructions
1. Use numbered lists for sequential steps
2. Start each step with an action verb
3. Include expected results
4. Provide screenshots for UI actions

#### Code Examples
- Use syntax highlighting for code blocks
- Include complete, runnable examples
- Explain what the code does
- Show expected output

## Language and Tone

### Voice
- **Professional but friendly** - Approachable expert
- **Direct and helpful** - Clear instructions without fluff
- **Encouraging** - Build user confidence

### Grammar Rules
- Use present tense for current functionality
- Use future tense only for upcoming features
- Use second person ("you") for instructions
- Use first person plural ("we") for recommendations

### Terminology

#### Consistent Terms
- **Westfall Personal Assistant** - Full application name (first use)
- **WPA** - Acceptable abbreviation after first use
- **application** - Not "app" in formal documentation
- **feature** - Not "function" or "tool" for UI elements
- **settings** - Not "preferences" or "options"

#### Avoiding Jargon
- Define technical terms on first use
- Link to glossary when appropriate
- Use common language alternatives when possible

## Formatting Standards

### Headers
- Use title case for H1 and H2
- Use sentence case for H3 and below
- Don't use punctuation in headers
- Keep headers descriptive and scannable

### Lists
- Use parallel structure in list items
- Start each item with same part of speech
- Use sentence case for list items
- End list items with periods only if they're complete sentences

### Links
- Use descriptive link text (not "click here")
- Link to the most specific relevant page
- Use relative links for internal documentation
- Test all links before publishing

### Code and Commands

#### Inline Code
Use backticks for:
- File names: `config.yaml`
- Commands: `python main.py`
- Code elements: `class MainWindow`
- Keyboard shortcuts: `Ctrl+C`

#### Code Blocks
```python
# Use language-specific syntax highlighting
def example_function():
    """Include docstrings and comments."""
    return "Complete examples preferred"
```

#### Command Line Examples
```bash
# Show the command prompt when helpful
$ python main.py --help

# Include expected output
Westfall Personal Assistant
Usage: python main.py [options]
```

### Tables
- Use tables for structured data comparison
- Include header row
- Keep cell content concise
- Ensure table is readable on mobile

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data     | Data     | Data     |

### Images and Media

#### Screenshots
- Use consistent browser/OS for screenshots
- Highlight relevant UI elements
- Include alt text for accessibility
- Keep file sizes reasonable (<500KB)

#### Diagrams
- Use consistent style and colors
- Include alt text descriptions
- Provide SVG format when possible
- Label all elements clearly

## Content Types

### User Guides
- Start with the user's goal
- Provide step-by-step instructions
- Include troubleshooting for common issues
- End with next steps or related topics

### API Documentation
- Include complete endpoint information
- Provide request/response examples
- Document all parameters and fields
- Include error codes and messages

### Tutorials
- Break complex tasks into steps
- Build complexity gradually
- Include checkpoints to verify progress
- Provide complete working examples

### Reference Material
- Organize alphabetically or logically
- Use consistent formatting
- Include cross-references
- Keep entries concise but complete

## Quality Checklist

Before publishing documentation:

### Content Review
- [ ] Information is accurate and current
- [ ] Examples work as written
- [ ] Links are functional
- [ ] Content matches the target audience
- [ ] Follows established templates

### Writing Review
- [ ] Clear and concise language
- [ ] Consistent terminology
- [ ] Proper grammar and spelling
- [ ] Appropriate tone and voice
- [ ] Scannable structure with headers

### Technical Review
- [ ] Code examples are tested
- [ ] Commands produce expected results
- [ ] Screenshots are current
- [ ] Front matter is complete
- [ ] Tags are appropriate

### Accessibility Review
- [ ] Alt text for all images
- [ ] Proper heading hierarchy
- [ ] Sufficient color contrast
- [ ] Descriptive link text
- [ ] Table headers identified

## Maintenance

### Regular Updates
- Review and update content quarterly
- Verify links and examples still work
- Update screenshots when UI changes
- Refresh "last_updated" dates

### Version Control
- Use clear commit messages
- Document major changes in changelog
- Tag releases for documentation versions
- Maintain backward compatibility when possible

## Tools and Resources

### Writing Tools
- **Markdown**: Standard format for all documentation
- **Vale**: Automated style checking
- **Grammarly**: Grammar and clarity checking
- **Hemingway**: Readability analysis

### Development Tools
- **Sphinx**: Documentation generation
- **MkDocs**: Alternative documentation platform
- **PlantUML**: Diagram creation
- **Screenshot tools**: Platform-specific tools

### References
- [Microsoft Writing Style Guide](https://docs.microsoft.com/en-us/style-guide/)
- [Google Developer Documentation Style Guide](https://developers.google.com/style)
- [Plain Language Guidelines](https://www.plainlanguage.gov/guidelines/)

---

*Last updated: September 8, 2025*