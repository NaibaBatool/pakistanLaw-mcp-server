# Pakistan Legal Document Collection

This directory contains verified statutory texts, legal provisions, and landmark summaries from official Pakistani legal repositories.

## Authoritative Sources

All included documents are sourced and cross-referenced from authoritative Pakistani portals:
- **The Pakistan Code**: [https://pakistancode.gov.pk](https://pakistancode.gov.pk) (Federal Ministry of Law and Justice)
- **National Assembly of Pakistan**: [https://na.gov.pk](https://na.gov.pk)
- **Senate of Pakistan**: [https://senate.gov.pk](https://senate.gov.pk)
- **Supreme Court of Pakistan**: [https://supremecourt.gov.pk](https://supremecourt.gov.pk)

## Included Acts & Statutes

1. **PECA 2016 (`peca_2016.json`)**: Prevention of Electronic Crimes Act 2016 (Cyber harassment, cyber stalking, unauthorized access, identity theft, defamation).
2. **PPC 1860 (`ppc_1860.json`)**: Pakistan Penal Code 1860 (Homicide, Cheating/Fraud, Harassment of women, Criminal intimidation, Defamation).
3. **Workplace Harassment Act 2010 (`harassment_workplace_2010.json`)**: Protection Against Harassment of Women at the Workplace Act 2010 (Inquiry committees, Ombudsman mechanism).
4. **Constitution 1973 (`constitution_1973.json`)**: Constitution of the Islamic Republic of Pakistan (Fundamental rights: Articles 4, 9, 10A, 14, 19, 19A, 25).
5. **CrPC 1898 (`crpc_1898.json`)**: Code of Criminal Procedure (FIR Section 154, Bail Sections 496, 497, 498).
6. **Family Courts Act 1964 (`family_courts_1964.json`)**: Family disputes, khula, maintenance, and child custody.

## Adding New Legal Documents

You can add new documents by creating a `.json` file in this directory following this schema:

```json
{
  "document_id": "UNIQUE-SLUG",
  "title": "Full Official Title of Act or Regulation",
  "short_title": "Colloquial or Short Title",
  "jurisdiction": "Pakistan (Federal or specific Province, e.g., Punjab / Sindh / KPK / Balochistan)",
  "source_type": "legislation | judgment | regulation | official_notice",
  "source_url": "https://pakistancode.gov.pk/...",
  "publication_date": "YYYY-MM-DD",
  "verification_status": "verified_statute",
  "description": "Brief description of statutory scope",
  "sections": [
    {
      "section_number": "Section Number / Article Number",
      "heading": "Section Heading",
      "text": "Exact, unamended verbatim text from official gazette",
      "keywords": ["keyword1", "keyword2"]
    }
  ]
}
```

Plain text (`.txt`) and Markdown (`.md`) files with YAML or structured headers are also supported by the loader.
