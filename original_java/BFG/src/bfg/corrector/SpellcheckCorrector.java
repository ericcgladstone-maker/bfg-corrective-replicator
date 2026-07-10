package bfg.corrector;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Random;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.search.spell.PlainTextDictionary;
import org.apache.lucene.search.spell.SpellChecker;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.common.base.MoreObjects;
import com.google.common.cache.Cache;
import com.google.common.cache.CacheBuilder;
import com.google.common.cache.CacheStats;

import bfg.MutationStep;

/*
 * Correction problem:
 * capitalization (the vs The)
 * hashtags (#TwoWords)
 * elite speak (733t h4x0r)
 * internet shorthand (lol, rtfm, etc.)
 * symbology in general (*nix, 4chan)
 */

public class SpellcheckCorrector implements Corrector {
	private static final Logger log = LoggerFactory.getLogger(SpellcheckCorrector.class);
	private static final String no_suggestion = "";
	private static final String word_regex = "([a-zA-Z0-9\\-']+)";

	private Directory dictionaryDirectory;
	private Path dictionaryFile;
	private int suggest_count;
	private float suggest_similarity;

	private Cache<String, List<String>> suggestCache = CacheBuilder.newBuilder().maximumSize(200000).recordStats()
			.build();
	private Random rng = new Random();

	public SpellcheckCorrector(int suggestCount, float suggestSimilarity, Path dictionaryFile, Path ndxDir) {
		log.debug("Creating");
		try {
			dictionaryDirectory = FSDirectory.open(ndxDir);
		} catch (IOException e) {
			log.error("Unable to configure corrector using index at " + ndxDir, e);
		}
		this.dictionaryFile = dictionaryFile;
		this.suggest_count = suggestCount;
		this.suggest_similarity = suggestSimilarity;
	}

	@Override
	public List<MutationStep> correct(List<MutationStep> generationList) {
		return Arrays.asList(correct(generationList.toArray(new MutationStep[0])));
	}

	private MutationStep correct(MutationStep step, SpellChecker spell) {
		String childString = step.getChildString();
		String correctedString = correct(childString, spell);
		if (!childString.equals(correctedString)) {
			log.trace("Corrected {} to {}", childString, correctedString);
			step.setChildString(correctedString);
		}
		return step;
	}

	public MutationStep[] correct(MutationStep[] generation) {
		long start = System.currentTimeMillis();
		try (SpellChecker spell = new SpellChecker(dictionaryDirectory)) {
			spell.indexDictionary(new PlainTextDictionary(dictionaryFile), new IndexWriterConfig(), false);
			Arrays.stream(generation).parallel().forEach(x -> correct(x, spell));
		} catch (IOException e) {
			log.error("Unable to apply corrections", e);
		}

		long stop = System.currentTimeMillis();
		log.debug("Correction time: {} for {} items", stop - start, generation.length);
		CacheStats stats = suggestCache.stats();
		log.debug("Suggest cache - hit rate {}, avg load penalty {}", stats.hitRate(),
				stats.averageLoadPenalty() / 1e9);
		return generation;
	}

	private String correct(String str, SpellChecker spell) {
		Pattern p = Pattern.compile(word_regex);
		Matcher m = p.matcher(str);
		StringBuffer bufStr = new StringBuffer();
		while (m.find()) {
			String word = m.group();
			m.appendReplacement(bufStr, suggest(word, spell));
		}
		m.appendTail(bufStr);
		String result = bufStr.toString();
		return result;
	}

	private String suggest(String word, SpellChecker spell) {
		try {
			if (spell.exist(word)) {
				log.trace("{} exists", word);
				return word;
			} else {
				String replacement;
				try {
					List<String> suggestionList = MoreObjects
							.firstNonNull(suggestCache.get(word, new Callable<List<String>>() {
								private final String[] no_suggestions = new String[] {};

								@Override
								public List<String> call() throws Exception {
									String[] suggestions = MoreObjects.firstNonNull(
											spell.suggestSimilar(word, suggest_count, suggest_similarity),
											no_suggestions);
									return Arrays.asList(suggestions);
								}
							}), Collections.emptyList());
					if (suggestionList.isEmpty()) {
						replacement = no_suggestion;
					} else {
						replacement = suggestionList.get(rng.nextInt(suggestionList.size()));
					}
				} catch (ExecutionException e) {
					log.error("Unable to load suggestions", e);
					replacement = no_suggestion;
				}
				if (replacement.equals(no_suggestion)) {
					log.trace("{} not found, no alternatives", word);
					return word;
				}
				log.trace("{} not found, suggesting {}", word, replacement);
				return replacement;
			}
		} catch (IOException e) {
			log.error("Unable to make suggestions for " + word, e);
			return word;
		}
	}

	@Override
	public String description() {
		return "Spell check corrector using dictionary " + dictionaryFile + " indexed at " + dictionaryDirectory;
	}

}
