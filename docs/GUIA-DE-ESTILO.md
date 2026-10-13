# Guia de estilo e formato dos livros Linvuu (A1–A2)

Vale para todos os livros. Leia inteiro antes de escrever.

## Princípios
- Gramática **prática e libertadora**: o aluno fala/escreve melhor ao fim de cada capítulo. Profundidade onde o ponto é difícil, clareza onde é fácil. Ordem natural (o que se precisa primeiro vem primeiro).
- Livros em português do Brasil para aprender inglês, espanhol, francês, italiano, alemão, russo. O livro de português para estrangeiros é escrito em **inglês**.
- Cada capítulo parte de um **problema que a língua materna do aluno cria** (a "armadilha").
- Exemplos vivos, naturais, de situações reais (albergue, trabalho, família, compras, viagem, redes). **Nada de frases-fantasma** ("A caneta da minha tia está na mesa"). Nada de exemplos copiados de livros-fonte.
- Português do Brasil natural ("você", "a gente" quando coloquial). Termo da escola brasileira + termo da língua estudada na primeira ocorrência.
- **Sem emoji, sem bandeiras, sem mascote.** Tom caloroso, direto, de professor que respeita o aluno. Sem "super", sem exclamações em excesso, sem promessas vazias.
- **Direito autoral:** as obras de referência servem só para conferir fatos e a ordem dos tópicos. Não copie trechos, não parafraseie de perto, não reaproveite os exemplos delas. Tudo aqui é redação própria.
- **Precisão acima de tudo.** Se não tem certeza de um fato linguístico (forma, exceção, registro), confira em fonte de referência ou escreva de modo que não afirme o que não sabe. Um erro numa gramática custa a confiança do aluno. Não invente exceções nem frequências.

## Anatomia de cada capítulo (livros em português)
Um arquivo `NN-cap.md` por capítulo. Estrutura exata:

```
# Capítulo N. Título (A1)           <- um único H1 por arquivo; (A1) ou (A2)

**Meta do capítulo.** Ao final, você ... (1–2 frases, verificável)

## 1. Cena: título curto
Uma linha de contexto.

::: dialogo
**Nome:** fala na língua-alvo
**Nome:** fala
:::

Tradução em português (uma linha corrida, com " / " entre falas).

Uma frase que mostra onde o ponto gramatical já apareceu na cena, sem jargão ainda.

## 2. A armadilha do português
Qual hábito do português induz o erro; mostre o contraste com 1–2 tabelas pequenas.

## 3. Descubra você mesmo
Quatro a seis exemplos para observar + 2 perguntas; a regra "aparece" logo abaixo.

## 4. Em 30 segundos
::::: dica
A regra que já funciona na conversa. Curta (4–8 linhas ou uma tabelinha).
:::::

## 5. Por dentro
A regra completa, com exceções reais e o critério de quando não vale.
Use tabelas de formas (colunas pequenas), blocos `::: atencao` para cuidados.

## 6. Frases de ouro
Tabela de duas colunas (língua-alvo | português natural), 8 linhas.

## 7. Treino em quatro degraus
::::: exercicio
**Degrau 1. Reconheça.** 7–8 itens de escolha.
**Degrau 2. Complete.** 8–10 lacunas (use \_\_\_\_).
**Degrau 3. Produza.** 3–4 tarefas livres curtas.
**Degrau 4. Corrija o erro típico.** 6–7 frases, uma delas certa.
:::::

## 8. O erro típico
Prosa curta + `::: erros` (tabela Errado | Certo | Por quê) com 3–6 linhas.

## 9. Retorno
Três perguntas de capítulos anteriores (revisão espaçada), seguidas de uma tabela
"Quando | O que fazer" (Dia 1, 3, 7, 14).

## 10. Resumo e “já consigo”
::::: resumo
Pontos-chave + **Já consigo?** com 3 afirmações verificáveis.
:::::

## Glossário do capítulo N
Tabela Língua-alvo | Português (15–25 itens do próprio capítulo, com artigo/gênero/forma-base).

## Chave comentada do capítulo N
::::: gabarito
Resposta de TODOS os itens, em ordem; nos itens que enganam, diga por que a errada tenta.
:::::
```

Tamanho-alvo: 2.500–4.500 palavras por capítulo (o piloto do professor tem ~1.800 e é o piso; vá além onde o tema é difícil, sem encher).

## Sintaxe Markdown aceita pelo conversor
- `{{texto}}` marca texto na língua-alvo dentro de frase (fonte própria). Em tabelas e diálogos também.
- Containers: `::: dialogo`, `::: atencao`, `::: erros`, `::: comparacao`, `::: passo 1 Título`, `::::: dica`, `::::: exercicio`, `::::: resumo`, `::::: gabarito` (o container externo tem mais dois-pontos que os internos).
- Tabelas em pipe (`| a | b |` + `|---|---|`). Sem HTML. Nada de `<br>` dentro de célula.
- Pronúncia entre crases: `` `ZHEH~-tchee` `` (somente nos livros de PLE).
- Riscado `~~assim~~` para forma errada; **negrito** para a parte que importa; *itálico* para termos e comentários.
- Sem imagens. Sem notas de rodapé. Sem links.

## Verificação antes de entregar
1. Releia cada exemplo: está correto, natural, de verdade?
2. Releia cada item da chave contra o enunciado (numeração, letras, resultados).
3. Todo exercício tem resposta única defensável; se admite mais de uma, a chave diz.
4. O capítulo não usa gramática que só aparece depois (ou, se usa, está sob a forma de bloco pronto, sem explicar).
