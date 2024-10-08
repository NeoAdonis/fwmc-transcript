Prompts have a token limit, so the following considerations have to be taken before including a word or phrase as part of them:

- Words that are frequently used in the transcripts but tend to have many different misspellings should be part of the prompt.
- If a word or phrase has a very common misspelling, it should go into the replacements list.
- Expressions or figures of speech that are uncommon in real life but common in a usual transcript should be part of the prompt.

For instance, the following content has been added to the prompt:

- Fuwawa & Mococo introductions: The introduction phrases teach the model FUWAMOCO's names. Full names (Fuwawa Abyssgard and Mococo Abyssgard) are used to that the model also learns the word 'Abyssgard'.
- "Ruffians": Teaches the model that this is word is used very frequently as a proper noun.
- "Use the hashtag #FWMCMorning": As they mention twice the word 'hashtag', this teaches the model to treat that as "hashtag #". "Use the" string is prepended so that the word "hashtag" can be spelled in lowercase. The entire usual expression "Please share your thoughts with..." is not needed and can be skipped to save tokens.
- Closing words: These are part of every FWMC Morning episode. Teaches the model some phrases that are uncommon in daily speech such as "Have a howl of a day".
- Very common names: Advent member names are commonly used and can get easily confused with a variety of English words by the model, thus being suitable candidates to be part of the prompt.

In contrast, the following content has been added instead to the list of expressions to replace via regular expressions:

- Proper/capitalized nouns: Replacement is easy enough.