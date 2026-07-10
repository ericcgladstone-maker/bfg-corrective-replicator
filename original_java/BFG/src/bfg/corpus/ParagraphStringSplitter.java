package bfg.corpus;

import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.text.BreakIterator;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aliasi.sentences.MedlineSentenceModel;
import com.aliasi.sentences.SentenceModel;
import com.aliasi.tokenizer.IndoEuropeanTokenizerFactory;
import com.aliasi.tokenizer.Tokenizer;
import com.aliasi.tokenizer.TokenizerFactory;

public class ParagraphStringSplitter {
	private static final Logger log = LoggerFactory.getLogger(ParagraphStringSplitter.class);

	private static final SentenceModel LP_SENTENCE_MODEL = new MedlineSentenceModel();
	private static final TokenizerFactory LP_TOKENIZER_FACTORY = IndoEuropeanTokenizerFactory.INSTANCE;

	public static void main(String[] args) throws IOException {

		if (args.length == 0) {
			String testText = "This is a test.  I have here Dr. Watson.  He is Sherlock Holmes' friend.";
			int sNum = 0;
			for (String sentence : new ParagraphStringSplitter().splitParagraph(testText)) {
				log.info("{} : {}", ++sNum, sentence);
			}
		} else {
			for (String arg : args) {
				byte[] encoded = Files.readAllBytes(Paths.get(arg));
				String fileText = new String(encoded, Charset.defaultCharset());
				log.info("{} :: length {}", arg, fileText.length());
				int sNum = 0;
				for (String sentence : new ParagraphStringSplitter().splitParagraph(fileText)) {
					log.info("{} : {}", ++sNum, sentence);
				}
				log.info("{} :: sentences {}", arg, sNum);
			}
		}

	}

	public Collection<String> splitParagraph(String para) {
		// return splitParagraph_BreakIterator(para);
		return splitParagraph_Lingpipe(para);
	}

	private Collection<String> splitParagraph_BreakIterator(String para) {
		ArrayList<String> sentences = new ArrayList<>();
		BreakIterator iter = BreakIterator.getSentenceInstance(Locale.US);
		iter.setText(para);
		int startPos = iter.first();
		int endPos = iter.next();
		do {
			sentences.add(para.substring(startPos, endPos));
			startPos = endPos;
			endPos = iter.next();
		} while (endPos != BreakIterator.DONE);
		return sentences;
	}

	private Collection<String> splitParagraph_Lingpipe(String para) {
		List<String> tokenList = new ArrayList<String>();
		List<String> whiteList = new ArrayList<String>();
		Tokenizer tokenizer = LP_TOKENIZER_FACTORY.tokenizer(para.toCharArray(), 0, para.length());
		tokenizer.tokenize(tokenList, whiteList);

		log.debug("{} TOKENS", tokenList.size());
		log.debug("{} WHITESPACES", whiteList.size());

		String[] tokens = new String[tokenList.size()];
		String[] whites = new String[whiteList.size()];
		tokenList.toArray(tokens);
		whiteList.toArray(whites);
		int[] sentenceBoundaries = LP_SENTENCE_MODEL.boundaryIndices(tokens, whites);

		log.debug("{} SENTENCE END TOKEN OFFSETS", sentenceBoundaries.length);

		if (sentenceBoundaries.length < 1) {
			log.debug("No sentence boundaries found.");
			return Collections.emptyList();
		} else {
			ArrayList<String> sentences = new ArrayList<>();
			int sentStartTok = 0;
			int sentEndTok = 0;
			for (int i = 0; i < sentenceBoundaries.length; ++i) {
				StringBuilder sb = new StringBuilder();
				sentEndTok = sentenceBoundaries[i];
				for (int j = sentStartTok; j <= sentEndTok; j++) {
					sb.append(tokens[j]).append(whites[j + 1]);
				}
				String sentence = sb.toString();
				log.debug("SENTENCE {}: {}", (i + 1), sentence);
				sentences.add(sentence);
				sentStartTok = sentEndTok + 1;
			}
			return sentences;
		}
	}
}
