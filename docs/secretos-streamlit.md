# Secretos para Streamlit Community Cloud

**Son opcionales.** Sin secretos, la app funciona completa: el informe para el comprador usa la **plantilla (modo sin API)**. Se probó así en local y en un entorno limpio.

Si quiere que el informe lo redacte Claude: en share.streamlit.io → la app → **Settings → Secrets**, pegue esto con **sus** valores (nunca en el repo):

```toml
ANTHROPIC_API_KEY = ""     # clave de console.anthropic.com
LLM_TOPE_USD = "0.50"      # tope de gasto por sesión de la app, en dólares
LLM_MODELO = "claude-opus-5-5"   # opcional; claude-haiku-5-5 cuesta unas 40 veces menos
```

Streamlit expone las claves del primer nivel también como variables de entorno, que es como las lee `chacra/informe.py`.
Si alguna vez una clave se filtra, revóquela en la consola de Anthropic y cree otra.
