package bfg;

import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashSet;
import java.util.List;
import java.util.Properties;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.common.base.CharMatcher;
import com.google.common.base.Splitter;

import bfg.evaluator.EvaluatorFactory;
import bfg.evaluator.WeaselEvaluator;

public class DictionaryUpdate {
	private static final Logger log = LoggerFactory.getLogger(DictionaryUpdate.class);

	private Properties props;

	public DictionaryUpdate(Properties props) {
		this.props = props;
	}

	public static void main(String[] args) {
		Properties props = new Properties();
		try (FileInputStream propFile = new FileInputStream(args[0])) {
			props.load(propFile);
		} catch (IOException ex) {
			String msg = "Could not load properties file " + args[0];
			log.error(msg, ex);
			throw new RuntimeException(msg, ex);
		}
		new DictionaryUpdate(props).run();
	}

	public void run() {
		WeaselEvaluator evaluator = (WeaselEvaluator) EvaluatorFactory.getInstance(this.props);
		Splitter wordSplitter = Splitter.on(CharMatcher.anyOf(" :-'\",;.?")).omitEmptyStrings().trimResults();
		Set<String> targetWords = new HashSet<>();
		evaluator.getTargets().stream().sequential()
				.forEach(sentence -> targetWords.addAll(wordSplitter.splitToList(sentence)));

		Set<String> sourceDictionaryWords = new HashSet<>();
		String sourceDictionaryFilename = props.getProperty("dictionary.update.source");
		try (Stream<String> stream = Files.lines(Paths.get(sourceDictionaryFilename), StandardCharsets.UTF_8)) {
			stream.forEach(sourceDictionaryWords::add);
		} catch (IOException e) {
			throw new RuntimeException("Could not open source dictionary " + sourceDictionaryFilename, e);
		}
		Set<String> newWords = new HashSet<>(targetWords);
		newWords.removeAll(sourceDictionaryWords);
		Set<String> combinedDictionaryWords = new HashSet<>(sourceDictionaryWords);
		combinedDictionaryWords.addAll(targetWords);
		log.info("Target sentences contain {} distinct words", targetWords.size());
		log.info("Source dictionary has {} entries", sourceDictionaryWords.size());
		log.info("{} target words are not in the dictionary", newWords.size());
		newWords.stream().sorted().forEachOrdered(newWord -> log.info("\tnew word : {}", newWord));
		List<String> newDictionaryWords = combinedDictionaryWords.stream().sorted().collect(Collectors.toList());
		String targetDictionaryFilename = props.getProperty("dictionary.update.target");
		try {
			Files.write(Paths.get(targetDictionaryFilename), newDictionaryWords, StandardCharsets.UTF_8);
		} catch (IOException e) {
			throw new RuntimeException("Error writing new dictionary file " + targetDictionaryFilename, e);
		}
		log.info("Wrote {} words to {}", newDictionaryWords.size(), targetDictionaryFilename);
	}
}
