package bfg.mutator;

import java.util.Properties;

public class MutatorFactory {
	private static final String PROP_SOURCE = "mutator.source";
	private static final String PROP_TARGET = "mutator.target";
	private static final String PROP_MUTATE_CHAR_CHANCE = "mutator.mutateCharChance";
	private static final String PROP_INSERT_CHAR_CHANCE = "mutator.insertCharChance";
	private static final String PROP_INSERT_SPACE_CHANCE = "mutator.insertSpaceChance";
	private static final String PROP_DELETE_CHAR_CHANCE = "mutator.deleteCharChance";
	private static final String PROP_DELETE_SPACE_CHANCE = "mutator.deleteSpaceChance";

	public static Mutator getInstance(Properties props) {
		return new Mutator(props.getProperty(PROP_SOURCE), props.getProperty(PROP_TARGET),
				Double.parseDouble(props.getProperty(PROP_MUTATE_CHAR_CHANCE)),
				Double.parseDouble(props.getProperty(PROP_INSERT_CHAR_CHANCE)),
				Double.parseDouble(props.getProperty(PROP_DELETE_CHAR_CHANCE)),
				Double.parseDouble(props.getProperty(PROP_INSERT_SPACE_CHANCE)),
				Double.parseDouble(props.getProperty(PROP_DELETE_SPACE_CHANCE)));
	}
}
