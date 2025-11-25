# Contributing to GAINS Food Vision API

Thank you for your interest in contributing! 🙏

## How to Contribute

### 1. Report Issues

Found a bug or have a feature request? Open an issue on GitHub.

### 2. Submit Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### 3. Code Style

- Follow PEP 8 for Python code
- Use type hints
- Add docstrings to functions and classes
- Keep functions focused and small

### 4. Testing

Run tests before submitting:

```bash
pytest tests/ -v
```

### 5. Documentation

- Update README.md if adding new features
- Add docstrings to new functions
- Update API documentation

## Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/gains-food-vision-api.git
cd gains-food-vision-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Download model
python tools/download_model.py

# Seed database
python seeds/import_cofid.py

# Run server
uvicorn main:app --reload
```

## Priority Areas

We'd especially appreciate contributions in these areas:

1. **Model Improvements**
   - Better Food-101 training
   - Additional datasets
   - Faster inference

2. **Data Sources**
   - Additional nutrition databases
   - Better label mappings
   - More aliases

3. **GAINS Scoring**
   - Refinement of scoring algorithm
   - Additional factors
   - Validation studies

4. **Performance**
   - Faster database queries
   - Better caching
   - Batch processing

5. **Testing**
   - More comprehensive tests
   - Integration tests
   - Load testing

## Questions?

Open an issue or contact the GAINS team.

Thank you for contributing! 💚
