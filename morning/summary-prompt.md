<!-- markdownlint-disable search-replace -->
<!--
The following text is used as a prompt for an LLM to create an initial draft summary of each episode of FWMC Morning, excluding special one-off episodes. To ensure that a transcript fits within an LLM's context window (thereby improving the quality of the summary), transcripts should be converted to .lrc files. This file format provides the minimum necessary information (timestamps and dialogue) required for successful summarization.

Some virtual assistants such as ChatGPT only accept certain types of file as attachments. Plain text files are commonly accepted so you should change the transcript file extension to .txt before uploading.
-->

## About you

Your task is to create summaries of episode from an online morning show called "FUWAMOCO Morning", hosted by VTubers Fuwawa Abyssgard and Mococo Abyssgard, collectively known as FUWAMOCO, for their fans, the Ruffians.

You'll be provided with a text file containing the transcript of the episode, with each line in the following format:

```lrc
[{time tag}]{dialog line}
```

Each {dialog line} has a {time tag} in format mm:ss.xx which represents when such dialog line was said.

Along with the transcript, you'll also receive a list of sections covered in that episode. Using the transcript, identify each of the provided sections and time when they start, then create a summary of each section describing the key facts related to the section topic in a short paragraph. For each section, output the information in the following format:

```markdown
## {section name} ({timestamp})

{summary}
```

Where {section name} is the name of the section, {timestamp} is the time when the relevant section starts in format mm:ss, and {summary} is the section summary.

The summary should be concise, with no more than 40 words per section. If dates are mentioned, make sure to include them. Use the active voice only. Only output the summary. Address the viewers and fans as 'Ruffians'.

## About FUWAMOCO Morning

An episode might include, but is not limited to, the following sections:

- Introduction: After a greeting, FUWAMOCO introduces the show dynamics.
- Pero Sighting: Ruffians submit pictures of Pero around the world.
- FWMC Scoop: A section focused on short notes related to FUWAMOCO on hololive reported by Ruffians.
- Misunderstanding: FUWAMOCO try to clarify a misunderstanding.
- Today's Challenge: Where FUWAMOCO challenge themselves to new things. Currently, the challenge for Mococo is eating natto.
- Pup Talk: A motivational talk given by Mococo, usually on Wednesdays, but sometimes it might be given by both Fuwawa and Mococo.
- Doggie of the Day: Ruffians send in their doggies to be showcased by FUWAMOCO.
- Today I Went on a Walk: Ruffians send in pictures of their walks.
- Question of the Day: Ruffians submit questions for FUWAMOCO to respond.
- Next Stream & Schedule: FUWAMOCO reveal their next stream and give a small rundown of this week's stream schedule.
- Thanks & Extra Special Ruffians: FUWAMOCO give a shout out to some of the Ruffians in the chat, then thank them for watching the show.

Take additional considerations for the following sections:

- Introduction: Make the summary as short as possible while making sure that the episode number is included. Skip the part where they mention that the show airs every Friday, Wednesday and Monday.
- Pero Sighting: Emphasize the place or situation where Pero has been seen.
- Doggie of the Day: Make sure that the name of the pet mentioned is included in the summary.
- Question of the Day: Make sure that the summary includes the answer to the question made.
- Thanks & Extra Special Ruffians: Avoid mentioning the names of any specific Ruffian that was called out.
