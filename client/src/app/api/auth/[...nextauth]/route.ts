import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";

async function refreshAccessToken(token: any) {
  try {
    const url =
      "https://oauth2.googleapis.com/token?" +
      new URLSearchParams({
        client_id: process.env.GOOGLE_CLIENT_ID!,
        client_secret: process.env.GOOGLE_CLIENT_SECRET!,
        grant_type: "refresh_token",
        refresh_token: token.refreshToken as string,
      });

    const response = await fetch(url, { method: "POST" });
    const refreshedTokens = await response.json();

    if (!response.ok) throw refreshedTokens;

    return {
      ...token,
      accessToken: refreshedTokens.access_token,
      accessTokenExpires: Date.now() + refreshedTokens.expires_in * 1000, // 1 hour
      refreshToken: refreshedTokens.refresh_token ?? token.refreshToken,
    };
  } catch (error) {
    console.error("Error refreshing access token", error);
    return {
      ...token,
      error: "RefreshAccessTokenError",
    };
  }
}

const handler = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          // ✅ Add Slides + Drive file access scopes
          scope: [
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/presentations",
            "https://www.googleapis.com/auth/drive.file",
          ].join(" "),
          access_type: "offline", // ensures refresh_token
          prompt: "consent", // forces consent screen for refresh_token
          response_type: "code",
        },
      },
    }),
  ],

  callbacks: {
    async jwt({ token, account, profile }) {
      // Initial sign-in
      if (account && profile) {
        return {
          accessToken: account.access_token,
          accessTokenExpires:
            Date.now() +
            (account.expires_in
              ? (account.expires_in as number) * 1000
              : 3600 * 1000),
          refreshToken: account.refresh_token,
          user: { id: profile.sub },
        };
      }

      // Return previous token if it's still valid
      if (Date.now() < (token.accessTokenExpires as number)) {
        return token;
      }

      // Access token has expired, refresh it
      return await refreshAccessToken(token);
    },

    async session({ session, token }) {
      session.accessToken = token.accessToken;
      session.error = token.error;
      if (session.user && token.user?.id) {
        session.user.id = token.user.id;
      }
      return session;
    },
  },

  pages: {
    signIn: "/signin",
  },

  session: {
    strategy: "jwt",
  },
});

export { handler as GET, handler as POST };
