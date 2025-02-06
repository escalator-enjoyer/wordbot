import discord
import asyncio
import os
from dotenv import load_dotenv
import requests
import random
from nltk.corpus import wordnet as wn
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from nltk.sentiment import SentimentIntensityAnalyzer

load_dotenv()

# https://www.mit.edu/~ecprice/wordlist.10000
TOKEN = os.environ['TOKEN']

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

sia = SentimentIntensityAnalyzer()

with open('words.txt', 'r+') as f:
  # f.write(requests.get('https://www.mit.edu/~ecprice/wordlist.10000').content.decode())
  words = f.read().split('\n')

def random_words(num=1):
  random.shuffle(words)
  return words[:num]

def random_car():
  return requests.get('https://api.thecatapi.com/v1/images/search').json()[0]['url']

def generate_text(model_dir, prompt_text, max_length=100, temperature=0.7, top_k=50, top_p=0.9):
  tokenizer = GPT2Tokenizer.from_pretrained(model_dir)
  model = GPT2LMHeadModel.from_pretrained(model_dir)

  inputs = tokenizer.encode(prompt_text, return_tensors='pt')
  attention_mask = inputs.ne(tokenizer.pad_token_id).long()
  outputs = model.generate(
    inputs, 
    max_length=max_length, 
    num_return_sequences=1, 
    temperature=temperature, 
    top_k=top_k, 
    top_p=top_p,
    pad_token_id=tokenizer.eos_token_id,
    do_sample=True,
    attention_mask=attention_mask,
    repetition_penalty=1.2,
    no_repeat_ngram_size=1
  )

  text = tokenizer.decode(outputs[0], skip_special_tokens=True)
  return text

model_dir = './model_output'

@client.event
async def on_ready():
  await client.change_presence(activity=discord.Game(name="Among Us 2"), status=discord.Status.idle)
  print('readied up: almonte')

@client.event
async def on_message(message):
  if message.author == client.user:
    return

  l_msg = message.content.strip().lower()

  if 'random word' in l_msg:
    word = random_words(1)[0]
    syns = wn.synsets(word)
    spain = wn.synsets('spain')
    final = ""
    if syns:
      final += syns[0].lemmas()[0].name() + "\n"
      final += syns[0].definition() + "\n"
      if syns[0].examples():
        final += syns[0].examples()[0] + "\n"
      final += 'similarity to "spain:" ' + str(round(syns[0].wup_similarity(spain[0]), 3))
    await message.channel.send(final)
  
  elif 'compare ' in l_msg:
    try:
      _, word1, word2 = l_msg.split()
      syns1 = wn.synsets(word1)
      syns2 = wn.synsets(word2)
      if syns1 and syns2:
        similarity = syns1[0].wup_similarity(syns2[0])
      else:
        await message.channel.send("i dont know one of those words")
        return
      if similarity is not None:
        await message.channel.send(f'similarity between "{syns1[0].lemmas()[0].name()}" and "{syns2[0].lemmas()[0].name()}": {round(similarity * 100, 3)}%')
      else:
        await message.channel.send(f'no similarity found between "{syns1[0].lemmas()[0].name()}" and "{syns2[0].lemmas()[0].name()}"')
    except Exception as e:
      await message.channel.send(f'use: compare word1 word2\n{e}')
  
  elif 'sillify ' in l_msg:
    _, words = l_msg.split(" ", 1)
    words = words.split(' ')
    message = await message.channel.send('working !')
    try:
      silly_words = []
      for word in words:
        synsets = wn.synsets(word)
        if synsets:
          options = synsets[0].lemmas()[1:]
          if options:
            synonym = random.choice(options).name()
            silly_words.append(synonym)
          else:
            silly_words.append(word)
        else:
          silly_words.append(word)
      await message.edit(content=' '.join(silly_words))
    except Exception as e:
      await message.edit(content=f'lie ({e})')
      
  elif l_msg.startswith('ai'):
    parts = l_msg.split(' ', 2)

    if len(parts) == 3 and parts[1].replace('.', '', 1).isdigit():
      temperature = float(parts[1])
      prompt = parts[2]
    else:
      temperature = 0.7
      prompt = l_msg.split(' ', 1)[1]
    
    message = await message.channel.send('working !')
    try:
      res = generate_text(model_dir, prompt, temperature=temperature, top_k=25, top_p=1).replace('\\n', '\n').split('\n', 1)[0]
      await message.edit(content=res)
    except:
      await message.channel.send('error !')
  
  elif 'analyze ' in l_msg:
    _, thing = l_msg.split(' ', 1)
    analysis = sia.polarity_scores(thing)
    analysis = f"""negative: {analysis['neg']}
neutral: {analysis['neu']}
positive: {analysis['pos']}
compound: {analysis['compound']}"""
    await message.channel.send(analysis)
  
  elif 'random car' in l_msg:
    await message.channel.send(random_car())

client.run(TOKEN)