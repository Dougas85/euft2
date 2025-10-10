# 🚛 EUFT - Efetividade na Utilização da Frota

**EUFT (Efetividade na Utilização da Frota)** é uma aplicação web desenvolvida em **Python (Flask)** para análise e cálculo da eficiência operacional da frota de veículos dos Correios, com base em arquivos CSV de **RDVO** e **OS**.  
O sistema permite visualizar, em tempo real, o desempenho diário e acumulado de cada unidade (GERAE), identificar veículos sem retorno e acompanhar indicadores de produtividade da frota.

🔗 **Acesso público:** [https://euft2.onrender.com](https://euft2.onrender.com)

---

## 📊 Funcionalidades Principais

- **Importação de arquivos RDVO e OS** em formato `.csv`
- **Cálculo automático do EUFT diário** (Efetividade de Utilização da Frota)
- **Análise por região (GERAE)** ou geral (todas as regiões)
- **Exibição dos veículos sem retorno** (mais de 7h após saída)
- **Agrupamento de dados por placa e dia**
- **Detecção de inconsistências e erros de lançamento**
- **Interface moderna e responsiva (Bootstrap 5)**

---

## ⚙️ Estrutura do Projeto

```
euft/
│
├── app.py                # Aplicação principal Flask
├── placas.py             # Listas de placas e lotações por região (GERAE)
├── templates/
│   ├── index.html        # Página principal da interface
│   └── resultado.html    # Página de exibição dos resultados
│
├── static/
│   ├── styles.css        # Estilos customizados
│   └── script.js         # Scripts auxiliares
│
├── requirements.txt      # Dependências do projeto
└── README.md             # Documentação do sistema
```

---

## 🧮 Como o cálculo do EUFT é realizado

O sistema processa os arquivos RDVO e OS e realiza as seguintes etapas:

1. **Filtragem de placas** conforme a região (GERAE) selecionada.  
2. **Cálculo do tempo de utilização e distância percorrida** por veículo e dia.  
3. **Verificação de lançamentos corretos** com base nos critérios operacionais.  
4. **Cálculo do EUFT individual e total:**

   \[
   EUFT = \frac{\text{Dias Corretos}}{\text{Dias Totais} + \text{Adicional}}
   \]


5. **Identificação de veículos sem retorno** (tempo decorrido > 7h após saída).

---

## 🧩 Arquivo `placas.py`

O arquivo `placas.py` contém todas as listas de placas utilizadas por cada GERAE, como por exemplo:

```python
# Exemplo: Região 1 (GERAE 01)
placas_scudo1 = [...]
placas_mobi1 = [...]
placas_analisadas1 = [...]
placas_especificas1 = [...]
placas_to_lotacao1 = {...}

# Exemplo: Região 2 (GERAE 02)
placas_scudo2 = [...]
placas_mobi2 = [...]
placas_analisadas2 = [...]
placas_especificas2 = [...]
placas_to_lotacao2 = {...}

# Dicionário de todas as regiões
regioes = {
    'Região 1': {
        'placas_scudo': placas_scudo1,
        'placas_analisadas': placas_analisadas1,
        'placas_especificas': placas_especificas1,
        'placas_mobi': placas_mobi1,
        'placas_to_lotacao': placas_to_lotacao1
    },
    'Região 2': {
        'placas_scudo': placas_scudo2,
        'placas_analisadas': placas_analisadas2,
        'placas_especificas': placas_especificas2,
        'placas_mobi': placas_mobi2,
        'placas_to_lotacao': placas_to_lotacao2
    }
}

# SPI (todas as regiões combinadas)
from itertools import chain

regioes['SPI'] = {
    'placas_scudo': list(set(chain.from_iterable(r['placas_scudo'] for r in regioes.values()))),
    'placas_analisadas': list(set(chain.from_iterable(r['placas_analisadas'] for r in regioes.values()))),
    'placas_especificas': list(set(chain.from_iterable(r['placas_especificas'] for r in regioes.values()))),
    'placas_mobi': list(set(chain.from_iterable(r['placas_mobi'] for r in regioes.values()))),
    'placas_to_lotacao': {k: v for r in regioes.values() for k, v in r['placas_to_lotacao'].items()}
}
```

---

## 🧰 Requisitos e Instalação

### 1️⃣ Clonar o repositório
```bash
git clone https://github.com/seuusuario/euft.git
cd euft
```

### 2️⃣ Criar o ambiente virtual
```bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
```

### 3️⃣ Instalar dependências
```bash
pip install -r requirements.txt
```

### 4️⃣ Executar localmente
```bash
flask run
```
Acesse: [http://localhost:5000](http://localhost:5000)

---

## ☁️ Deploy no Render

O projeto está preparado para execução na **plataforma Render** (deploy automático a partir do GitHub).

**Passos para publicação:**
1. Faça login em [https://render.com](https://render.com)  
2. Clique em **“New +” → Web Service**  
3. Conecte o repositório do GitHub  
4. Configure:
   - **Environment:** Python 3.x  
   - **Build Command:** `pip install -r requirements.txt`  
   - **Start Command:** `gunicorn app:app`  
5. Clique em **Deploy Web Service**

Render irá gerar a URL pública (ex: `https://euft2.onrender.com`).

---


## 👨‍💻 Autor

**Douglas Francisco da Silva**  
Desenvolvimento e Análise de Dados — Correios  
📍 Brasil  
💬 [LinkedIn](www.linkedin.com/in/douglas-francisco-da-silva-51953435a)

---

## 🧠 Licença

Este projeto é de uso interno e institucional.  
Distribuição restrita para fins de monitoramento operacional da frota.
