# vocab_manager.py

import json
import time
import random
from groq import Groq
import os

class GermanVocabManager:
    def __init__(self):
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.example_refresh_threshold = 3  # Number of times a word is asked before refreshing example

    def create_empty_json(self, filename='german_vocab.json'):
        """Creates an empty JSON file if it doesn't exist."""
        with open(filename, 'w') as f:
            json.dump([], f)
        return f"{filename} created as an empty file."

    def load_vocabulary(self, filename='german_vocab.json'):
        """Loads vocabulary from a JSON file or creates the file if it doesn't exist."""
        if not os.path.exists(filename):
            self.create_empty_json(filename)
            return []

        try:
            with open(filename, 'r') as f:
                vocabulary = json.load(f)
            return self.update_vocab_structure(vocabulary)
        except json.JSONDecodeError:
            return []

    def update_vocab_structure(self, vocabulary):
        """Update the structure of vocabulary entries"""
        for word in vocabulary:
            if 'category' not in word:
                word['category'] = 'new'
            if 'times_asked' not in word:
                word['times_asked'] = 0
            if 'last_asked' not in word:
                word['last_asked'] = 0
            if 'previous_example' not in word:
                word['previous_example'] = None
            if 'last_example_refresh' not in word:
                word['last_example_refresh'] = 0
            if 'example_history' not in word:
                word['example_history'] = []
        return vocabulary

    def save_vocabulary(self, vocabulary, filename='german_vocab.json'):
        """Save vocabulary to JSON file"""
        with open(filename, 'w') as f:
            json.dump(vocabulary, f)

    def check_answer(self, word_entry, user_answer):
        """Check answer using LLM"""
        base_prompt = f"""
        German Word: {word_entry['word']}
        Correct Definition: {word_entry['definition']}
        User's Answer: {user_answer}
        """
        
        if word_entry['part_of_speech'] == 'noun':
            base_prompt += f"\nCorrect Gender: {word_entry['gender']}"
        
        prompt = base_prompt + """
        Evaluate if the user's answer matches the correct definition. For nouns, also check if they correctly identified the gender.
        The answer should be considered correct if the meaning is accurately conveyed, even if the exact wording is different.
        Start the response like this:
        Your answer is correct/incorrect!
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Error checking answer: {e}")
            return "Error evaluating answer. Please try again."

    def generate_new_example(self, word_entry):
        """Generate a new example sentence using LLM"""
        # Create a context that includes previous examples to ensure variety
        previous_examples = [word_entry['example']]
        if word_entry.get('previous_example'):
            previous_examples.append(word_entry['previous_example'])
        if word_entry.get('example_history'):
            previous_examples.extend(word_entry['example_history'])
        
        previous_examples_str = "\n".join(previous_examples)
        
        context = f"""
        Create a new, simple example sentence in German using the word "{word_entry['word']}".
        
        Word information:
        - Type: {word_entry['part_of_speech']}
        - {"Gender: " + word_entry['gender'] if word_entry['part_of_speech'] == 'noun' else ""}
        - Definition: {word_entry['definition']}
        
        Previous examples (create something different):
        {previous_examples_str}

        Rules:
        - Provide only the new example sentence in German
        - Make it simple and practical for learning
        - Use common vocabulary
        - Keep the sentence length moderate
        - Do not explain or translate, just provide the sentence
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": context}],
                model="llama3-8b-8192",
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating new example: {e}")
            return word_entry['example']  # Return the current example if generation fails

    def should_refresh_example(self, word_entry):
        """Check if the example should be refreshed based on times_asked"""
        times_asked = word_entry.get('times_asked', 0)
        last_example_refresh = word_entry.get('last_example_refresh', 0)
        times_since_refresh = times_asked - last_example_refresh
        return times_since_refresh >= self.example_refresh_threshold

    def categorize_answer(self, llm_response):
        """Determine category based on LLM response"""
        return "correct" if "correct" in llm_response.lower() else "incorrect"

    def increment_times_asked(self, word):
        """Increment the times a word has been asked and update example if needed"""
        word['times_asked'] = word.get('times_asked', 0) + 1
        word['last_asked'] = int(time.time())
        
        # Initialize tracking fields if they don't exist
        if 'last_example_refresh' not in word:
            word['last_example_refresh'] = 0
        if 'example_history' not in word:
            word['example_history'] = []
            
        # Check if we should refresh the example
        if self.should_refresh_example(word):
            try:
                new_example = self.generate_new_example(word)
                if new_example and new_example != word['example']:
                    # Store the current example in history
                    if word['example'] not in word['example_history']:
                        word['example_history'].append(word['example'])
                    # Keep only the last 5 examples in history
                    word['example_history'] = word['example_history'][-5:]
                    # Update the current and previous examples
                    word['previous_example'] = word['example']
                    word['example'] = new_example
                    word['last_example_refresh'] = word['times_asked']
            except Exception as e:
                print(f"Error updating example: {e}")

    def get_next_word_index(self, vocabulary, consecutive_new_incorrect):
        """Get the index of the next word to practice"""
        if not vocabulary:
            return None

        priorities = []
        current_time = int(time.time())
        
        for i, word in enumerate(vocabulary):
            category = word.get('category', 'new')
            times_asked = word.get('times_asked', 0)
            last_asked = word.get('last_asked', 0)
            time_since_last = current_time - last_asked

            # Base priority score
            if category == 'new':
                priority = 100
            elif category == 'incorrect':
                priority = 80
            else:  # correct
                priority = 60

            # Adjust priority based on various factors
            priority -= times_asked * 5  # Reduce priority for frequently asked words
            priority += time_since_last / 3600  # Increase priority for words not asked recently
            
            # Bonus for words that haven't been asked in a long time
            if time_since_last > 86400:  # More than a day
                priority += 20
            
            priorities.append((i, priority))

        # Sort words by priority (highest to lowest)
        sorted_priorities = sorted(priorities, key=lambda x: x[1], reverse=True)
        top_words = sorted_priorities[:5]

        # If we've had too many consecutive new/incorrect words, force a correct one
        if consecutive_new_incorrect >= 4:
            correct_words = [i for i, _ in top_words if vocabulary[i]['category'] == 'correct']
            if correct_words:
                return random.choice(correct_words)

        # Otherwise, choose randomly from the top 5
        return random.choice([i for i, _ in top_words])

    def create_new_word_entry(self, word, part_of_speech, definition, example, gender=None):
        """Create a new vocabulary entry"""
        entry = {
            "word": word,
            "part_of_speech": part_of_speech,
            "definition": definition,
            "example": example,
            "previous_example": None,
            "example_history": [],
            "category": "new",
            "times_asked": 0,
            "last_asked": 0,
            "last_example_refresh": 0
        }
        if gender:
            entry["gender"] = gender
        return entry

    def update_word_entry(self, word_entry, word, part_of_speech, definition, example, gender=None):
        """Update an existing vocabulary entry"""
        # Preserve the history and tracking fields
        history_fields = {
            'times_asked': word_entry.get('times_asked', 0),
            'last_asked': word_entry.get('last_asked', 0),
            'category': word_entry.get('category', 'new'),
            'previous_example': word_entry.get('previous_example', None),
            'example_history': word_entry.get('example_history', []),
            'last_example_refresh': word_entry.get('last_example_refresh', 0)
        }
        
        # Update the main fields
        word_entry.update({
            'word': word,
            'part_of_speech': part_of_speech,
            'definition': definition,
            'example': example,
            **history_fields  # Preserve history fields
        })
        
        # Handle gender field
        if gender:
            word_entry['gender'] = gender
        elif 'gender' in word_entry:
            del word_entry['gender']
            
        return word_entry

    def get_word_statistics(self, word_entry):
        """Get statistics for a word entry"""
        return {
            'times_asked': word_entry.get('times_asked', 0),
            'last_asked': time.strftime('%Y-%m-%d %H:%M:%S', 
                                      time.localtime(word_entry.get('last_asked', 0))),
            'category': word_entry.get('category', 'new'),
            'example_count': len(word_entry.get('example_history', [])) + 1,
            'last_refresh': time.strftime('%Y-%m-%d %H:%M:%S', 
                                        time.localtime(word_entry.get('last_example_refresh', 0)))
        }