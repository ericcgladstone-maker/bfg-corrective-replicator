package bfg.corrector;

import java.nio.file.Paths;
import java.util.Properties;

public class CorrectorFactory {
	private static final String PROP_TYPENAME = "corrector";

	private static final String PROP_SC_DICTIONARY_FILE = "corrector.spellcheck.dictionaryFile";
	private static final String PROP_SC_DICTIONARY_NDX = "corrector.spellcheck.dictionaryIndex";
	private static final String PROP_SC_SUGGESTIONS = "corrector.spellcheck.suggestions";
	private static final String PROP_SC_SUGGEST_SIMILARITY = "corrector.spellcheck.suggestion.similarity";

	private static final String PROP_SCnN_NULLCHANCE = "corrector.spellchecknull.nullchance";
	private static final String PROP_SCnN_SCCHANCE = "corrector.spellchecknull.spellcheckchance";
	private static final String PROP_SCnN_SUGGESTIONS = "corrector.spellchecknull.suggestions";
	private static final String PROP_SCnN_SUGGEST_SIMILARITY = "corrector.spellchecknull.suggestion.similarity";
	private static final String PROP_SCnN_DICTIONARY_FILE = "corrector.spellchecknull.dictionaryFile";
	private static final String PROP_SCnN_DICTIONARY_NDX = "corrector.spellchecknull.dictionaryIndex";

	public static Corrector getInstance(Properties props) {
		String type = props.getProperty(PROP_TYPENAME);
		Corrector corrector;
		if ("Spellcheck".equals(type)) {
			corrector = new SpellcheckCorrector(Integer.parseInt(props.getProperty(PROP_SC_SUGGESTIONS), 10),
					Float.parseFloat(props.getProperty(PROP_SC_SUGGEST_SIMILARITY)),
					Paths.get(props.getProperty(PROP_SC_DICTIONARY_FILE)),
					Paths.get(props.getProperty(PROP_SC_DICTIONARY_NDX)));
		} else if ("Null".equals(type)) {
			corrector = new NullCorrector();
		} else if ("Spellcheck_and_Null".equals(type)) {
			return new CompoundCorrector( //
					new CompoundCorrectorStep(new NullCorrector(),
							Double.parseDouble(props.getProperty(PROP_SCnN_NULLCHANCE, "1.0"))), //
					new CompoundCorrectorStep(
							new SpellcheckCorrector(Integer.parseInt(props.getProperty(PROP_SCnN_SUGGESTIONS), 10),
									Float.parseFloat(props.getProperty(PROP_SCnN_SUGGEST_SIMILARITY)),
									Paths.get(props.getProperty(PROP_SCnN_DICTIONARY_FILE)),
									Paths.get(props.getProperty(PROP_SCnN_DICTIONARY_NDX))),
							Double.parseDouble(props.getProperty(PROP_SCnN_SCCHANCE, "1.0"))) //
			);
		} else {
			throw new RuntimeException("Unknown evaluator type");
		}
		return corrector;
	}
}
