package bfg.misc;

public class StringSanitizer {
	private static StringSanitizer instance = null;

	private StringSanitizer() {
	}

	public static StringSanitizer getInstance() {
		synchronized (StringSanitizer.class) {
			if (instance == null) {
				instance = new StringSanitizer();
			}
		}
		return instance;
	}

	public String sanitize(String str) {
		return str //
				.toLowerCase() //
				.replace(',', ' ') //
				.replace(';', ' ') //
				.replace(':', ' ') //
				.replace('.', ' ') //
				.replace('?', ' ') //
				.replace('!', ' ') //
				.replaceAll("  ", " ") //
				.trim() //
		;
	}
}
